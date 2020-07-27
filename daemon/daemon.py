from time import sleep, time
from threading import Thread
from queue import Queue
from xmlrpc.client import ServerProxy
from pathlib import Path

import zmq

from rotor_control.rotors import Rotor
from radio_control.radio_task_starter import RadioProcessTask, RadioSaveRawTask
from utilities.object_tracker import EphemerisTracker
from utilities.yaml_tools import validate_yaml_schema, load_yaml
from utilities.functions import azel_within_range


class SmallRadioTelescopeDaemon:
    def __init__(self, config_directory):
        validate_yaml_schema(path=config_directory)
        config_dict = load_yaml(path=config_directory)

        self.station = config_dict["STATION"]
        self.contact = config_dict["EMERGENCY_CONTACT"]
        self.az_limits = (
            config_dict["AZLIMITS"]["lower_bound"],
            config_dict["AZLIMITS"]["upper_bound"],
        )
        self.el_limits = (
            config_dict["ELLIMITS"]["lower_bound"],
            config_dict["ELLIMITS"]["upper_bound"],
        )
        self.stow_location = (
            config_dict["STOW_LOCATION"]["azimuth"],
            config_dict["STOW_LOCATION"]["elevation"],
        )
        self.motor_offsets = (
            config_dict["MOTOR_OFFSETS"]["azimuth"],
            config_dict["MOTOR_OFFSETS"]["elevation"],
        )
        self.motor_type = config_dict["MOTOR_TYPE"]
        self.motor_port = config_dict["MOTOR_PORT"]
        self.radio_center_frequency = config_dict["RADIO_CF"]
        self.radio_sample_frequency = config_dict["RADIO_SF"]
        self.radio_num_bins = config_dict["RADIO_NUM_BINS"]
        self.radio_integ_cycles = config_dict["RADIO_INTEG_CYCLES"]
        self.beamwidth = config_dict["BEAMWIDTH"]
        self.temp_sys = config_dict["TSYS"]
        self.temp_cal = config_dict["TCAL"]
        self.save_dir = config_dict["SAVE_DIRECTORY"]

        self.ephemeris_tracker = EphemerisTracker(
            self.station["latitude"],
            self.station["longitude"],
            config_file=str(Path(config_directory, "sky_coords.csv").absolute()),
        )
        self.ephemeris_locations = self.ephemeris_tracker.get_all_azimuth_elevation()
        self.ephemeris_cmd_location = None

        self.rotor = Rotor(
            self.motor_type,
            self.motor_port,
            self.az_limits,
            self.el_limits,
            *self.motor_offsets,
        )
        self.rotor_location = self.stow_location
        self.rotor_cmd_location = self.stow_location

        self.rpc_server = ServerProxy("http://localhost:5557/")
        self.radio_process_task = RadioProcessTask(
            num_bins=self.radio_num_bins, num_integrations=self.radio_integ_cycles
        )
        self.radio_save_raw_task = None

        self.current_queue_item = "None"
        self.command_queue = Queue()
        self.command_error_logs = []

    def log_message(self, message):
        self.command_error_logs.append((time(), message))
        print(message)

    def update_ephemeris_location(self):
        while True:
            self.ephemeris_tracker.update_all_az_el()
            self.ephemeris_locations = (
                self.ephemeris_tracker.get_all_azimuth_elevation()
            )
            if self.ephemeris_cmd_location is not None:
                new_rotor_cmd_location = self.ephemeris_locations[
                    self.ephemeris_cmd_location
                ]
                if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
                    self.rotor_cmd_location = new_rotor_cmd_location
                else:
                    self.log_message(
                        f"Object {self.ephemeris_cmd_location} moved out of motor bounds"
                    )
                    self.ephemeris_cmd_location = None
            sleep(5)

    def update_rotor_status(self):
        while True:
            try:
                if not azel_within_range(
                    self.rotor_location, self.rotor_cmd_location
                ):
                    self.rotor.set_azimuth_elevation(*self.rotor_cmd_location)
                    start_time = time()
                    while (
                        not azel_within_range(
                            self.rotor_location, self.rotor_cmd_location
                        )
                        and (time() - start_time) < 10
                    ):
                        self.rotor_location = self.rotor.get_azimuth_elevation()
                        self.rpc_server.set_motor_az(float(self.rotor_location[0]))
                        self.rpc_server.set_motor_el(float(self.rotor_location[1]))
                        sleep(1)
                else:
                    self.rotor_location = self.rotor.get_azimuth_elevation()
                    self.rpc_server.set_motor_az(float(self.rotor_location[0]))
                    self.rpc_server.set_motor_el(float(self.rotor_location[1]))
                    sleep(1)
            except AssertionError as e:
                self.log_message(str(e))

    def update_command_queue(self):
        context = zmq.Context()
        command_port = 5556
        command_socket = context.socket(zmq.PULL)
        command_socket.bind("tcp://*:%s" % command_port)
        while True:
            self.command_queue.put(command_socket.recv_string())

    def update_status(self):
        context = zmq.Context()
        status_port = 5555
        status_socket = context.socket(zmq.PUB)
        status_socket.bind("tcp://*:%s" % status_port)
        while True:
            status = {
                "beam_width": self.beamwidth,
                "location": self.station,
                "motor_azel": self.rotor_location,
                "motor_cmd_azel": self.rotor_cmd_location,
                "object_locs": self.ephemeris_locations,
                "az_limits": self.az_limits,
                "el_limits": self.el_limits,
                "center_frequency": self.radio_center_frequency,
                "bandwidth": self.radio_sample_frequency,
                "motor_offsets": self.motor_offsets,
                "queued_item": self.current_queue_item,
                "queue_size": self.command_queue.qsize(),
                "emergency_contact": self.contact,
                "error_logs": self.command_error_logs,
            }
            status_socket.send_json(status)
            sleep(0.5)

    def srt_daemon_main(self):
        ephemeris_tracker_thread = Thread(
            target=self.update_ephemeris_location, daemon=True
        )
        rotor_pointing_thread = Thread(target=self.update_rotor_status, daemon=True)
        command_queueing_thread = Thread(target=self.update_command_queue, daemon=True)
        status_thread = Thread(target=self.update_status, daemon=True)

        try:
            self.radio_process_task.start()
        except RuntimeError as e:
            self.log_message(str(e))
        sleep(5)

        radio_params = {
            "Frequency": (self.rpc_server.set_freq, self.radio_center_frequency),
            "Sample Rate": (self.rpc_server.set_samp_rate, self.radio_sample_frequency),
            "Motor Azimuth": (self.rpc_server.set_motor_az, self.rotor_location[0]),
            "Motor Elevation": (self.rpc_server.set_motor_el, self.rotor_location[1]),
            "Is Running": (self.rpc_server.set_is_running, True),
        }
        for name in radio_params:
            method, value = radio_params[name]
            self.log_message(f"Setting {name} to {value}")
            method(value)
            sleep(0.1)

        ephemeris_tracker_thread.start()
        rotor_pointing_thread.start()
        command_queueing_thread.start()
        status_thread.start()

        keep_running = True

        while keep_running:
            try:
                self.current_queue_item = "None"
                command = self.command_queue.get()
                self.log_message(f"Running Command {command}")
                self.current_queue_item = command
                if command[0] == "*":
                    continue
                command_parts = command.split(" ")
                command_name = command_parts[0].lower()
                if command_parts[0] in self.ephemeris_locations:
                    new_rotor_cmd_location = self.ephemeris_locations[command_parts[0]]
                    if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
                        self.ephemeris_cmd_location = command_parts[0]
                        self.rotor_cmd_location = new_rotor_cmd_location
                        while not azel_within_range(
                            self.rotor_location, self.rotor_cmd_location
                        ):
                            sleep(0.1)
                    else:
                        self.log_message(
                            f"Object {command_parts[0]} Not in Motor Bounds"
                        )
                        self.ephemeris_cmd_location = None
                elif command_name == "stow":
                    self.ephemeris_cmd_location = None
                    self.rotor_cmd_location = self.stow_location
                    while not azel_within_range(
                        self.rotor_location, self.rotor_cmd_location
                    ):
                        sleep(0.1)
                elif command_name == "calibrate":
                    pass  # TODO: Implement Calibration Routine
                elif command_name == "quit":
                    keep_running = False
                    self.rpc_server.set_is_running(False)
                elif command_name == "record":
                    if self.radio_save_raw_task is None:
                        self.radio_save_raw_task = RadioSaveRawTask(
                            self.radio_sample_frequency, self.save_dir
                        )
                        self.radio_save_raw_task.start()
                    else:
                        self.log_message("Cannot Start Recording - Already Recording")
                elif command_name == "roff":
                    if self.radio_save_raw_task is not None:
                        self.radio_save_raw_task.terminate()
                        self.radio_save_raw_task = None
                elif command_name == "freq":
                    self.rpc_server.set_freq(float(command_parts[1]) * pow(10, 6))
                    self.radio_center_frequency = float(command_parts[1]) * pow(10, 6)
                elif command_name == "samp":
                    if self.radio_save_raw_task is not None:
                        self.radio_save_raw_task.terminate()
                    self.radio_sample_frequency = float(command_parts[1]) * pow(10, 6)
                    self.rpc_server.set_samp_rate(self.radio_sample_frequency)
                    if self.radio_save_raw_task is not None:
                        self.radio_save_raw_task = RadioSaveRawTask(
                            self.radio_sample_frequency, self.save_dir
                        )
                        self.radio_save_raw_task.start()
                elif command_name == "azel":
                    self.ephemeris_cmd_location = None
                    new_rotor_cmd_location = (
                        float(command_parts[1]),
                        float(command_parts[2]),
                    )
                    if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
                        self.rotor_cmd_location = new_rotor_cmd_location
                        while not azel_within_range(
                            self.rotor_location, self.rotor_cmd_location
                        ):
                            sleep(0.1)
                    else:
                        self.log_message(
                            f"Object at {new_rotor_cmd_location} Not in Motor Bounds"
                        )
                elif command_name == "offset":
                    self.motor_offsets = (
                        float(command_parts[1]),
                        float(command_parts[2]),
                    )
                    self.rotor.az_offset = float(command_parts[1])
                    self.rotor.el_offset = float(command_parts[2])
                elif command_name == "wait":
                    sleep(int(command_parts[1]))
                else:
                    self.log_message(f"Command Not Identified '{command}'")

            except IndexError as e:
                self.log_message(str(e))
            except ValueError as e:
                self.log_message(str(e))
            except ConnectionRefusedError as e:
                self.log_message(str(e))

        self.rotor_cmd_location = self.stow_location
        while not azel_within_range(self.rotor_location, self.rotor_cmd_location):
            sleep(0.1)
        if self.radio_save_raw_task is not None:
            self.radio_save_raw_task.terminate()
            self.radio_save_raw_task = None
        self.radio_process_task.terminate()


if __name__ == "__main__":
    daemon = SmallRadioTelescopeDaemon(config_directory="./config/")
    daemon.srt_daemon_main()
