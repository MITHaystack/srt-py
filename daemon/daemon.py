from time import sleep, time
from threading import Thread
from queue import Queue
from xmlrpc.client import ServerProxy

import zmq

from rotor_control.rotors import Rotor
from radio_utils.radio_task_starter import start_save_raw, stop_save_raw
from utilities.object_tracker import EphemerisTracker
from utilities.yaml_tools import validate_yaml_schema, load_yaml
from utilities.functions import azel_within_range


validate_yaml_schema()
config_dict = load_yaml()

station = config_dict["STATION"]
contact = config_dict["EMERGENCY_CONTACT"]
az_limits = (
    config_dict["AZLIMITS"]["lower_bound"],
    config_dict["AZLIMITS"]["upper_bound"],
)
el_limits = (
    config_dict["ELLIMITS"]["lower_bound"],
    config_dict["ELLIMITS"]["upper_bound"],
)
stow_location = (
    config_dict["STOW_LOCATION"]["azimuth"],
    config_dict["STOW_LOCATION"]["elevation"],
)
motor_offsets = (
    config_dict["MOTOR_OFFSETS"]["azimuth"],
    config_dict["MOTOR_OFFSETS"]["elevation"],
)
motor_type = config_dict["MOTOR_TYPE"]
motor_port = config_dict["MOTOR_PORT"]
radio_center_frequency = config_dict["RADIO_CF"]
radio_sample_frequency = config_dict["RADIO_SF"]
beamwidth = config_dict["BEAMWIDTH"]
temp_sys = config_dict["TSYS"]
temp_cal = config_dict["TCAL"]
save_dir = config_dict["SAVE_DIRECTORY"]

ephemeris_tracker = EphemerisTracker(
    station["latitude"], station["longitude"], config_file="./config/sky_coords.csv"
)
ephemeris_locations = ephemeris_tracker.get_all_azimuth_elevation()
ephemeris_cmd_location = None

rotor = Rotor(motor_type, motor_port, az_limits, el_limits, *motor_offsets)
rotor_location = stow_location
rotor_cmd_location = stow_location

rpc_server = ServerProxy("http://localhost:5557/")
current_queue_item = "None"
command_queue = Queue()
command_error_logs = []


def log_message(message):
    command_error_logs.append((time(), message))
    print(message)


def update_ephemeris_location():
    global ephemeris_locations
    global rotor_cmd_location
    global ephemeris_cmd_location
    while True:
        ephemeris_tracker.update_all_az_el()
        ephemeris_locations = ephemeris_tracker.get_all_azimuth_elevation()
        if ephemeris_cmd_location is not None:
            new_rotor_cmd_location = ephemeris_locations[ephemeris_cmd_location]
            if rotor.angles_within_bounds(*new_rotor_cmd_location):
                rotor_cmd_location = new_rotor_cmd_location
            else:
                log_message(f"Object {ephemeris_cmd_location} moved out of motor bounds")
                ephemeris_cmd_location = None
        sleep(5)


def update_rotor_status():
    global rotor_location
    while True:
        rotor.set_azimuth_elevation(*rotor_cmd_location)
        sleep(1)
        rotor_location = rotor.get_azimuth_elevation()
        rpc_server.set_motor_az(float(rotor_location[0]))
        rpc_server.set_motor_el(float(rotor_location[1]))
        sleep(0.1)


def update_command_queue():
    global command_queue
    context = zmq.Context()
    command_port = 5556
    command_socket = context.socket(zmq.PULL)
    command_socket.bind("tcp://*:%s" % command_port)
    while True:
        command_queue.put(command_socket.recv_string())


def update_status():
    context = zmq.Context()
    status_port = 5555
    status_socket = context.socket(zmq.PUB)
    status_socket.bind("tcp://*:%s" % status_port)
    while True:
        status = {
            "beam_width": beamwidth,
            "location": station,
            "motor_azel": rotor_location,
            "motor_cmd_azel": rotor_cmd_location,
            "object_locs": ephemeris_locations,
            "az_limits": az_limits,
            "el_limits": el_limits,
            "center_frequency": radio_center_frequency,
            "bandwidth": radio_sample_frequency,
            "motor_offsets": motor_offsets,
            "queued_item": current_queue_item,
            "queue_size": command_queue.qsize(),
            "emergency_contact": contact,
            "error_logs": command_error_logs
        }
        status_socket.send_json(status)
        sleep(0.5)


def srt_daemon_main():
    global current_queue_item
    global ephemeris_cmd_location
    global rotor_cmd_location
    global motor_offsets
    global radio_center_frequency
    global radio_sample_frequency

    ephemeris_tracker_thread = Thread(target=update_ephemeris_location, daemon=True)
    rotor_pointing_thread = Thread(target=update_rotor_status, daemon=True)
    command_queueing_thread = Thread(target=update_command_queue, daemon=True)
    status_thread = Thread(target=update_status, daemon=True)

    radio_params = {
        "Frequency": (rpc_server.set_freq, radio_center_frequency),
        "Sample Rate": (rpc_server.set_samp_rate, radio_sample_frequency),
        # "FFT Size": (rpc_server.set_fft_size, 8192),
        "Num Integrations": (rpc_server.set_num_integrations, 1000),
        "Motor Azimuth": (rpc_server.set_motor_az, rotor_location[0]),
        "Motor Elevation": (rpc_server.set_motor_el, rotor_location[1]),
        "Is Running": (rpc_server.set_is_running, True),
    }
    for name in radio_params:
        method, value = radio_params[name]
        log_message(f"Setting {name} to {value}")
        method(value)
        sleep(0.1)

    ephemeris_tracker_thread.start()
    rotor_pointing_thread.start()
    command_queueing_thread.start()
    status_thread.start()

    keep_running = True

    while keep_running:
        try:
            current_queue_item = "None"
            command = command_queue.get()
            log_message(f"Running Command {command}")
            current_queue_item = command
            if command[0] == "*":
                continue
            command_parts = command.split(" ")
            command_name = command_parts[0].lower()
            if command_parts[0] in ephemeris_locations:
                new_rotor_cmd_location = ephemeris_locations[command_parts[0]]
                if rotor.angles_within_bounds(*new_rotor_cmd_location):
                    ephemeris_cmd_location = command_parts[0]
                    rotor_cmd_location = new_rotor_cmd_location
                    while not azel_within_range(rotor_location, rotor_cmd_location):
                        sleep(0.1)
                else:
                    log_message(f"Object {command_parts[0]} Not in Motor Bounds")
                    ephemeris_cmd_location = None
            elif command_name == "stow":
                ephemeris_cmd_location = None
                rotor_cmd_location = stow_location
                while not azel_within_range(rotor_location, rotor_cmd_location):
                    sleep(0.1)
            elif command_name == "calibrate":
                pass  # TODO: Implement Calibration Routine
            elif command_name == "quit":
                keep_running = False
                rpc_server.set_is_running(False)
            elif command_name == "record":
                start_save_raw(radio_sample_frequency, save_dir)
            elif command_name == "roff":
                stop_save_raw()
            elif command_name == "freq":
                rpc_server.set_freq(float(command_parts[1]) * pow(10, 6))
                radio_center_frequency = float(command_parts[1]) * pow(10, 6)
            elif command_name == "samp":
                was_running = stop_save_raw()
                rpc_server.set_samp_rate(float(command_parts[1]) * pow(10, 6))
                radio_sample_frequency = float(command_parts[1]) * pow(10, 6)
                if was_running:
                    start_save_raw(radio_sample_frequency, save_dir)
            elif command_name == "azel":
                ephemeris_cmd_location = None
                new_rotor_cmd_location = (
                    float(command_parts[1]),
                    float(command_parts[2]),
                )
                if rotor.angles_within_bounds(*new_rotor_cmd_location):
                    rotor_cmd_location = new_rotor_cmd_location
                    while not azel_within_range(rotor_location, rotor_cmd_location):
                        sleep(0.1)
                else:
                    log_message(f"Object at {new_rotor_cmd_location} Not in Motor Bounds")
            elif command_name == "offset":
                motor_offsets = (float(command_parts[1]), float(command_parts[2]))
                rotor.az_offset = float(command_parts[1])
                rotor.el_offset = float(command_parts[2])
            elif command_name == "wait":
                sleep(int(command_parts[1]))
            else:
                log_message(f"Command Not Identified '{command}'")

        except IndexError as e:
            log_message(str(e))
        except ValueError as e:
            log_message(str(e))
        except ConnectionRefusedError as e:
            log_message(str(e))

    rotor_cmd_location = stow_location
    while not azel_within_range(rotor_location, rotor_cmd_location):
        sleep(0.1)


if __name__ == "__main__":
    srt_daemon_main()
