from time import sleep
from threading import Thread
from queue import Queue

import zmq

from rotor_control.rotors import Rotor
from utilities.object_tracker import EphemerisTracker
from utilities.yaml_tools import validate_yaml_schema, load_yaml


validate_yaml_schema()
config_dict = load_yaml()

station = config_dict["STATION"]
az_limits = (
    config_dict["AZLIMITS"]["lower_bound"],
    config_dict["AZLIMITS"]["upper_bound"],
)
el_limits = (
    config_dict["ELLIMITS"][   "lower_bound"],
    config_dict["ELLIMITS"]["upper_bound"],
)
stow_location = (
    config_dict["STOW_LOCATION"]["azimuth"],
    config_dict["STOW_LOCATION"]["elevation"]
)
beamwidth = config_dict["BEAMWIDTH"]
motor_type = config_dict["MOTOR_TYPE"]
motor_port = config_dict["MOTOR_PORT"]
temp_sys = config_dict["TSYS"]
temp_cal = config_dict["TCAL"]

ephemeris_tracker = EphemerisTracker(
    station["latitude"], station["longitude"], config_file="./config/sky_coords.csv"
)
ephemeris_locations = ephemeris_tracker.get_all_azimuth_elevation()
ephemeris_cmd_location = None

# rotor = Rotor(motor_type, motor_port, az_limits, el_limits)
rotor_location = stow_location
rotor_cmd_location = stow_location

command_queue = Queue()


def update_ephemeris_location():
    global ephemeris_locations
    global rotor_cmd_location
    while True:
        ephemeris_locations = ephemeris_tracker.get_all_azimuth_elevation()
        if ephemeris_cmd_location is not None:
            rotor_cmd_location = ephemeris_locations[ephemeris_cmd_location]
        sleep(5)


def update_rotor_status():
    global rotor_location
    while True:
        rotor.set_azimuth_elevation(*rotor_cmd_location)
        sleep(1)
        rotor_location = rotor.get_azimuth_elevation()
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
    status_port = 5554
    status_socket = context.socket(zmq.PUB)
    status_socket.bind("tcp://*:%s" % status_port)
    while True:
        status = {"beam_width": beamwidth, "location": station, "motor_azel": rotor_location,
                  "motor_cmd_azel": rotor_cmd_location, "object_locs": ephemeris_locations,
                  "az_limits": az_limits, "el_limits": el_limits}
        # status["center_frequency"] =
        # status["bandwidth"] =
        status_socket.send_json(status)
        sleep(0.5)


def srt_daemon_main():
    ephemeris_tracker_thread = Thread(target=update_ephemeris_location, daemon=True)
    rotor_pointing_thread = Thread(target=update_rotor_status, daemon=True)
    command_queueing_thread = Thread(target=update_command_queue, daemon=True)
    status_thread = Thread(target=update_status, daemon=True)

    ephemeris_tracker_thread.start()
    # rotor_pointing_thread.start()
    command_queueing_thread.start()
    status_thread.start()

    while True:
        try:
            command = command_queue.get()
            if command[0] == "*":
                continue
            command_parts = command.split(" ")
            command_name = command_parts[0].lower()
            if command_name == "sourcename":
                global ephemeris_cmd_location
                if command_parts[1] in ephemeris_locations:
                    ephemeris_cmd_location = command_parts[1]
                else:
                    raise ValueError
            elif command_name == "stow":
                global rotor_cmd_location
                ephemeris_cmd_location = None
                rotor_cmd_location = stow_location
            elif command_name == "calibrate":
                pass  # TODO: Implement Calibration Routine
            elif command_name == "quit":
                pass  # TODO: Decide on if/what quit should do
            elif command_name == "record":
                pass  # TODO: Implement
            elif command_name == "roff":
                pass  # TODO: Implement
            elif command_name == "freq":
                pass  # TODO: Implement
            elif command_name == "azel":
                ephemeris_cmd_location = None
                rotor_cmd_location = (float(command_parts[1]), float(command_parts[2]))
            elif command_name == "wait":
                sleep(int(command_parts[1]))

        except IndexError as e:
            print(e)
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    srt_daemon_main()
