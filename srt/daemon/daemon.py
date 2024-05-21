"""daemon.py

Main Control and Orchestration Class for the Small Radio Telescope

"""

from time import sleep, time
from datetime import timedelta, datetime, timezone
from threading import Thread
from queue import Queue
from xmlrpc.client import ServerProxy
from pathlib import Path
from operator import add

import zmq
import json
import numpy as np

from .rotor_control.rotors import Rotor
from .radio_control.radio_task_starter import (
    RadioProcessTask,
    RadioSaveRawTask,
    RadioCalibrateTask,
    RadioSaveSpecRadTask,
    RadioSaveSpecFitsTask,
)
from .utilities.object_tracker import EphemerisTracker
from .utilities.functions import azel_within_range, get_spectrum, is_square

import subprocess
from math import sqrt, ceil


class SmallRadioTelescopeDaemon:
    """
    Controller Class for the Small Radio Telescope
    """

    def __init__(self, config_directory, config_dict):
        """Initializer for the Small Radio Telescope Daemon

        Parameters
        ----------
        config_directory : str
            Path to the Directory Containing Configuration Files
        config_dict : dict
            Dictionary Containing SRT Settings
        """

        # Store Individual Settings In Object
        self.config_directory = config_directory
        self.station = config_dict["STATION"]
        self.contact = config_dict["EMERGENCY_CONTACT"]
        self.az_limits = (
            config_dict["AZLIMITS"]["lower_bound"],
            config_dict["AZLIMITS"]["upper_bound"],
        )
        if abs(self.az_limits[0] - self.az_limits[1]) > 360:
            print("Distance between AZLIMITS is greater than 360 deg. Consider lowering the upper limit.")
        self.el_limits = (
            config_dict["ELLIMITS"]["lower_bound"],
            config_dict["ELLIMITS"]["upper_bound"],
        )
        if abs(self.el_limits[0] - self.el_limits[1]) > 90:
            print("Distance between ELLIMITS is greater than 90 deg. Consider lowering the upper limit.")
        self.stow_location = (
            config_dict["STOW_LOCATION"]["azimuth"],
            config_dict["STOW_LOCATION"]["elevation"],
        )
        self.cal_location = (
            config_dict["CAL_LOCATION"]["azimuth"],
            config_dict["CAL_LOCATION"]["elevation"],
        )
        self.horizon_points = [
            (point["azimuth"], point["elevation"])
            for point in config_dict["HORIZON_POINTS"]
        ]
        self.motor_type = config_dict["MOTOR_TYPE"]
        self.motor_port = config_dict["MOTOR_PORT"]
        self.motor_baudrate = config_dict["MOTOR_BAUDRATE"]
        self.radio_center_frequency = config_dict["RADIO_CF"]
        self.radio_sample_frequency = config_dict["RADIO_SF"]
        self.radio_frequency_correction = config_dict["RADIO_FREQ_CORR"]
        self.radio_num_bins = config_dict["RADIO_NUM_BINS"]
        self.radio_integ_cycles = config_dict["RADIO_INTEG_CYCLES"]
        self.radio_autostart = config_dict["RADIO_AUTOSTART"]
        self.num_beamswitches = config_dict["NUM_BEAMSWITCHES"]
        self.beamwidth = config_dict["BEAMWIDTH"]
        self.temp_sys = config_dict["TSYS"]
        self.temp_cal = config_dict["TCAL"]
        self.save_dir = config_dict["SAVE_DIRECTORY"]
        self.npoint_integration_time = config_dict["NPOINT_INTEG_TIME"]
        self.minimal_arrows_distance = config_dict["NPOINT_INTEG_TIME"]
        self.play_sounds = config_dict["PLAY_SOUNDS"]
        self.npoint_arrows = config_dict["NPOINT_ARROWS"]
        self.waterfall_length = config_dict["WATERFALL_LENGTH"]
        self.gui_timezone = config_dict["GUI_TIMEZONE"]
        if self.gui_timezone != "UTC" and self.gui_timezone != "local":
            print("Unknows value of GUI_TIMEZONE: \'" + self.gui_timezone + "\'. It has to be \'UTC\' or \'local\'. Defaulting to UTC.")
            self.gui_timezone = "UTC"
        self.display_lim = (
            config_dict["DISPLAY_LIM"]["az_lower_display_lim"],
            config_dict["DISPLAY_LIM"]["az_upper_display_lim"],
            config_dict["DISPLAY_LIM"]["el_lower_display_lim"],
            config_dict["DISPLAY_LIM"]["el_upper_display_lim"],
        )
        self.draw_ecliptic = config_dict["DRAW_ECLIPTIC"]
        self.draw_equator = config_dict["DRAW_EQUATOR"]
        self.n_pnt_count = config_dict["N_PNT_COUNT"]

        # Generate Default Calibration Values
        # Values are Set Up so that Uncalibrated and Calibrated Spectra are the Same Values
        # Unless there is a pre-exisiting calibration from a previous run
        self.cal_values = [1.0 for _ in range(self.radio_num_bins)]
        self.cal_power = 1.0 / (self.temp_sys + self.temp_cal)
        calibration_path = Path(config_directory, "calibration.json")
        if calibration_path.is_file():
            with open(calibration_path, "r") as input_file:
                try:
                    cal_data = json.load(input_file)
                    # If Calibration is of a Different Size Than The Current FFT Size, Discard
                    if len(cal_data["cal_values"]) == self.radio_num_bins:
                        self.cal_values = cal_data["cal_values"]
                        self.cal_power = cal_data["cal_pwr"]
                except KeyError:
                    pass

        # Create Helper Object Which Tracks Celestial Objects
        self.ephemeris_tracker = EphemerisTracker(
            self.station["latitude"],
            self.station["longitude"],
            config_file=str(Path(config_directory, "sky_coords.csv").absolute()),
        )
        self.ephemeris_locations = self.ephemeris_tracker.get_all_azimuth_elevation()
        self.ephemeris_vlsr = self.ephemeris_tracker.get_all_vlsr()
        self.current_vlsr = 0.0
        self.ephemeris_cmd_location = None

        # Create Rotor Command Helper Object
        self.rotor = Rotor(
            self.motor_type,
            self.motor_port,
            self.motor_baudrate,
            self.az_limits,
            self.el_limits,
        )
        self.rotor_location = self.stow_location
        self.rotor_destination = self.stow_location
        self.rotor_offsets = (0.0, 0.0)
        self.rotor_cmd_location = tuple(
            map(add, self.rotor_destination, self.rotor_offsets)
        )

        # Create Radio Processing Task (Wrapper for GNU Radio Script)
        self.radio_process_task = RadioProcessTask(
            num_bins=self.radio_num_bins, num_integrations=self.radio_integ_cycles
        )
        self.radio_queue = Queue()
        self.radio_save_task = None

        # Create Object for Keeping Track of What Commands Are Running or Have Failed
        self.current_queue_item = "None"
        self.command_queue = Queue()
        self.command_error_logs = []
        self.keep_running = True

        # List for data that will be plotted in the app
        self.n_point_data = []
        self.beam_switch_data = []
        self.rotor_loc_npoint_live = []

    def log_message(self, message):
        """Writes Contents to a Logging List and Prints

        Parameters
        ----------
        message : str
            Message to Log and Print

        Returns
        -------
        None
        """
        self.command_error_logs.insert(0, (time(), message))
        print(message)

    def n_point_scan(self, n_pnt_count, object_id):
        """Runs an N-Point Scan About an Object

        Parameters
        ----------
        object_id : str
            Name of the Object to Perform N-Point Scan About

        Returns
        -------
        None
        """
        if n_pnt_count < 4:
            print("The value of N_PNT_COUNT is <4. Scan may not work.")
        if is_square(n_pnt_count) == False:
            print("The value of N_PNT_COUNT is not a square of a natural number. Scan may not work.")
        self.ephemeris_cmd_location = None
        self.radio_queue.put(("soutrack", object_id))
        # Send vlsr to radio queue
        cur_vlsr = self.ephemeris_vlsr[object_id]
        self.radio_queue.put(("vlsr", float(cur_vlsr)))
        self.current_vlsr = cur_vlsr
        rotor_loc = []
        pwr_list = []
        scan_center_list = []
        np_sides = [sqrt(n_pnt_count), sqrt(n_pnt_count)]
        for scan in range(n_pnt_count):
            current_scan_center = self.ephemeris_locations[object_id]
            scan_center_list.append(current_scan_center)
            self.log_message("{0} of {1} point scan.".format(scan + 1, n_pnt_count))
            i = (scan // sqrt(n_pnt_count)) - 2
            j = (scan % sqrt(n_pnt_count)) - 2
            el_dif = i * self.beamwidth * 0.5
            az_dif_scalar = np.cos((current_scan_center[1] + el_dif) * np.pi / 180.0)
            # Avoid issues where you get close to the zenith
            if np.abs(az_dif_scalar)<1e-4:
                az_dif = 0
            else:
                az_dif = j * self.beamwidth * 0.5 / az_dif_scalar
    
            new_rotor_offsets = (az_dif, el_dif)

            if self.rotor.angles_within_bounds(*current_scan_center):
                self.rotor_destination = current_scan_center
                self.point_at_offset(*new_rotor_offsets)
            rotor_loc.append(self.rotor_location)
            self.rotor_loc_npoint_live = rotor_loc
            sleep(self.npoint_integration_time)
            raw_spec = get_spectrum(port=5561)
            p = np.sum(raw_spec)
            a = len(raw_spec)
            pwr = (self.temp_sys + self.temp_cal) * p / (a * self.cal_power)
            pwr_list.append(pwr)
        maxdiff = (az_dif, el_dif)

        sc_az = [t[0] for t in scan_center_list]
        sc_el = [t[1] for t in scan_center_list]
        sc_az_mean = sum(sc_az)/len(sc_az)
        sc_el_mean = sum(sc_el)/len(sc_el)
        scan_center = (sc_az_mean, sc_el_mean)

        self.n_point_data = [scan_center, maxdiff, rotor_loc, pwr_list, np_sides]

        # add code to collect spectrum data.
        self.rotor_offsets = (0.0, 0.0)
        self.ephemeris_cmd_location = object_id

        if self.play_sounds == True:
            try:
                subprocess.call(['speech-dispatcher'], stdout=subprocess.DEVNULL)
                subprocess.call(['spd-say', '"N-point scan has finished"'])
            except:
                print("""Sounds are enabled in the config file, but there was a problem and could not play sound.
                      (The playback mechanism uses Ubuntu's speech dispatcher).""")


    def beam_switch(self, object_id):
        """Swings Antenna Across Object

        Parameters
        ----------
        object_id : str
            Name of the Object to Perform Beam-Switch About

        Returns
        -------
        None
        """
        self.ephemeris_cmd_location = None
        self.radio_queue.put(("soutrack", object_id))
        # Send vlsr to radio queue
        cur_vlsr = self.ephemeris_vlsr[object_id]
        self.radio_queue.put(("vlsr", float(cur_vlsr)))
        self.current_vlsr = cur_vlsr
        new_rotor_destination = self.ephemeris_locations[object_id]
        rotor_loc = []
        pwr_list = []
        for j in range(0, (3 * self.num_beamswitches)-1):
            if (j == 0) or ((j+1) % 3 == 0):
                if j==0:
                    self.log_message("{0} of {1} beam switch.".format(ceil((j + 1)/3),   self.num_beamswitches)) 
                else:
                    self.log_message("{0} of {1} beam switch.".format(ceil((j + 1)/3)+1, self.num_beamswitches))
            self.radio_queue.put(("beam_switch", j + 1))
            az_dif_scalar = np.cos(new_rotor_destination[1] * np.pi / 180.0)
            az_dif = (j % 3 - 1) * self.beamwidth / az_dif_scalar
            new_rotor_offsets = (az_dif, 0)
            if self.rotor.angles_within_bounds(*new_rotor_destination):
                self.rotor_destination = new_rotor_destination
                self.point_at_offset(*new_rotor_offsets)
            rotor_loc.append(self.rotor_location)
            sleep(5)
            raw_spec = get_spectrum(port=5561)
            p = np.sum(raw_spec)
            a = len(raw_spec)
            pwr = (self.temp_sys + self.temp_cal) * p / (a * self.cal_power)
            pwr_list.append(pwr)
        self.rotor_offsets = (0.0, 0.0)
        self.radio_queue.put(("beam_switch", 0))
        self.ephemeris_cmd_location = object_id
        self.beam_switch_data = [rotor_loc, pwr_list]

    def point_at_object(self, object_id):
        """Points Antenna Directly at Object, and Sets Up Tracking to Follow it

        Parameters
        ----------
        object_id : str
            Name of Object to Point at and Track

        Returns
        -------
        None
        """
        self.rotor_offsets = (0.0, 0.0)
        self.radio_queue.put(("soutrack", object_id))
        # Send vlsr to radio queue
        cur_vlsr = self.ephemeris_vlsr[object_id]
        self.radio_queue.put(("vlsr", float(cur_vlsr)))
        self.current_vlsr = cur_vlsr
        new_rotor_cmd_location = self.ephemeris_locations[object_id]
        if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
            self.ephemeris_cmd_location = object_id
            self.rotor_destination = new_rotor_cmd_location
            self.rotor_cmd_location = new_rotor_cmd_location
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location):
                sleep(0.1)
        else:
            self.log_message(f"Object {object_id} Not in Motor Bounds")
            self.ephemeris_cmd_location = None

    def point_at_azel(self, az, el):
        """Points Antenna at a Specific Azimuth and Elevation

        Parameters
        ----------
        az : float
            Azimuth, in degrees, to turn antenna towards
        el : float
            Elevation, in degrees, to point antenna upwards at

        Returns
        -------
        None
        """
        # cur_vlsr = self.ephemeris_tracker.calculate_vlsr_azel((az,el))
        # self.radio_queue.put(("vlsr",cur_vlsr))
        # self.current_vlsr = cur_vlsr
        self.ephemeris_cmd_location = None
        self.rotor_offsets = (0.0, 0.0)
        # Send az and el angles to sources track for the radio
        self.radio_queue.put(("soutrack", f"azel_{az}_{el}"))
        # Send vlsr to radio queue
        cur_vlsr = self.ephemeris_tracker.calculate_vlsr_azel((az, el))
        self.current_vlsr = cur_vlsr
        self.radio_queue.put(("vlsr", float(cur_vlsr)))

        new_rotor_destination = (az, el)
        new_rotor_cmd_location = new_rotor_destination
        if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
            self.rotor_destination = new_rotor_destination
            self.rotor_cmd_location = new_rotor_cmd_location
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location):
                sleep(0.1)
        else:
            self.log_message(f"Object at {new_rotor_cmd_location} Not in Motor Bounds")

    def point_at_offset(self, az_off, el_off):
        """From the Current Object or Position Pointed At, Move to an Offset of That Location

        Parameters
        ----------
        az_off : float
            Number of Degrees in Azimuth Offset
        el_off : float
            Number of Degrees in Elevation Offset

        Returns
        -------
        None
        """
        new_rotor_offsets = (az_off, el_off)
        new_rotor_cmd_location = tuple(
            map(add, self.rotor_destination, new_rotor_offsets)
        )
        if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
            self.rotor_offsets = new_rotor_offsets
            self.rotor_cmd_location = new_rotor_cmd_location
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location):
                sleep(0.1)
        else:
            self.log_message(f"Offset {new_rotor_offsets} Out of Bounds")

    def stow(self):
        """Moves the Antenna Back to Its Stow Location

        Returns
        -------
        None
        """
        self.ephemeris_cmd_location = None
        self.radio_queue.put(("soutrack", "at_stow"))
        self.rotor_offsets = (0.0, 0.0)
        self.rotor_destination = self.stow_location
        self.rotor_cmd_location = self.stow_location
        while not azel_within_range(self.rotor_location, self.rotor_cmd_location):
            sleep(0.1)

    def calibrate(self):
        """Runs Calibration Processing and Pushes New Values to Processing Script

        Returns
        -------
        None
        """
        sleep(
            self.radio_num_bins * self.radio_integ_cycles / self.radio_sample_frequency
        )
        radio_cal_task = RadioCalibrateTask(
            self.radio_num_bins,
            self.config_directory,
        )
        radio_cal_task.start()
        radio_cal_task.join(30)
        path = Path(self.config_directory, "calibration.json")
        with open(path, "r") as input_file:
            cal_data = json.load(input_file)
            self.cal_values = cal_data["cal_values"]
            self.cal_power = cal_data["cal_pwr"]
        self.radio_queue.put(("cal_pwr", self.cal_power))
        self.radio_queue.put(("cal_values", self.cal_values))
        self.log_message("Calibration Done")

    def start_recording(self, name):
        """Starts Recording Data

        Parameters
        ----------
        name : str
            Name of the File to Be Recorded

        Returns
        -------
        None
        """
        if self.radio_save_task is None:
            if name is None:
                self.radio_save_task = RadioSaveRawTask(
                    self.radio_sample_frequency, self.save_dir, name
                )
            elif name.endswith(".rad"):
                name = None if name == "*.rad" else name
                self.radio_save_task = RadioSaveSpecRadTask(
                    self.radio_sample_frequency,
                    self.radio_num_bins,
                    self.save_dir,
                    name,
                )
            elif name.endswith(".fits"):
                name = None if name == "*.fits" else name
                self.radio_save_task = RadioSaveSpecFitsTask(
                    self.radio_sample_frequency,
                    self.radio_num_bins,
                    self.save_dir,
                    name,
                )
            else:
                self.radio_save_task = RadioSaveRawTask(
                    self.radio_sample_frequency, self.save_dir, name
                )
            self.radio_save_task.start()
        else:
            self.log_message("Cannot Start Recording - Already Recording")

    def stop_recording(self):
        """Stops Any Current Recording, if Running

        Returns
        -------
        None
        """
        if self.radio_save_task is not None:
            self.radio_save_task.terminate()
            self.radio_save_task = None

    def set_freq(self, frequency):
        """Set the Frequency of the Processing Script

        Parameters
        ----------
        frequency : float
            Center Frequency, in Hz, to Set SDR to

        Returns
        -------
        None
        """
        self.radio_center_frequency = frequency  # Set Local Value
        self.radio_queue.put(
            ("freq", self.radio_center_frequency + self.radio_frequency_correction)
        )  # Push Update to GNU Radio

    def set_samp_rate(self, samp_rate):
        """Set the Sample Rate of the Processing Script

        Note that this stops any currently running raw saving tasks

        Parameters
        ----------
        samp_rate : float
            Sample Rate for the SDR in Hz

        Returns
        -------
        None
        """
        if self.radio_save_task is not None:
            self.radio_save_task.terminate()
        self.radio_sample_frequency = samp_rate
        self.radio_queue.put(("samp_rate", self.radio_sample_frequency))

    def quit(self):
        """Stops the Daemon Process

        Returns
        -------
        None
        """
        self.keep_running = False
        self.radio_queue.put(("is_running", self.keep_running))

    def play_sound(self, command):
        """Declaims a text

        Parameters
        ----------
        command : string
            Text to declaim

        Returns
        -------
        None
        """
        if self.play_sounds == True:
            command = command.replace('playsound ', '')
            command = "\"" + command + "\""
            try:
                subprocess.call(['speech-dispatcher'], stdout=subprocess.DEVNULL)
                subprocess.call(['spd-say', command])
            except:
                print("""Sounds are enabled in the config file, but there was a problem and could not play sound.
                      (The playback mechanism uses Ubuntu's speech dispatcher).""")

    def update_ephemeris_location(self):
        """Periodically Updates Object Locations for Tracking Sky Objects

        Is Operated as an Infinite Looping Thread Function

        Returns
        -------
        None
        """
        last_updated_time = None
        while True:
            if last_updated_time is None or time() - last_updated_time > 10:
                last_updated_time = time()
                self.ephemeris_tracker.update_all_az_el()
            self.ephemeris_locations = (
                self.ephemeris_tracker.get_all_azimuth_elevation()
            )
            self.ephemeris_vlsr = self.ephemeris_tracker.get_all_vlsr()
            if self.ephemeris_cmd_location is not None:
                new_rotor_destination = self.ephemeris_locations[
                    self.ephemeris_cmd_location
                ]
                self.current_vlsr = self.ephemeris_vlsr[self.ephemeris_cmd_location]
                new_rotor_cmd_location = tuple(
                    map(add, new_rotor_destination, self.rotor_offsets)
                )
                if self.rotor.angles_within_bounds(
                    *new_rotor_destination
                ) and self.rotor.angles_within_bounds(*new_rotor_cmd_location):
                    self.rotor_destination = new_rotor_destination
                    self.rotor_cmd_location = new_rotor_cmd_location
                else:
                    self.log_message(
                        f"Object {self.ephemeris_cmd_location} moved out of motor bounds"
                    )
                    self.ephemeris_cmd_location = None
            sleep(1)

    def update_rotor_status(self):
        """Periodically Sets Rotor Azimuth and Elevation and Fetches New Antenna Position

        Is Operated as an Infinite Looping Thread Function

        Returns
        -------
        None
        """
        while True:
            try:
                current_rotor_cmd_location = self.rotor_cmd_location
                if not azel_within_range(
                    self.rotor_location, current_rotor_cmd_location
                ):
                    self.rotor.set_azimuth_elevation(*current_rotor_cmd_location)
                    sleep(1)
                    start_time = time()
                    while (
                        not azel_within_range(
                            self.rotor_location, current_rotor_cmd_location
                        )
                    ) and (time() - start_time) < 10:
                        past_rotor_location = self.rotor_location
                        self.rotor_location = self.rotor.get_azimuth_elevation()
                        if not self.rotor_location == past_rotor_location:
                            g_lat, g_lon = self.ephemeris_tracker.convert_to_gal_coord(
                                self.rotor_location
                            )
                            self.radio_queue.put(
                                ("motor_az", float(self.rotor_location[0]))
                            )
                            self.radio_queue.put(
                                ("motor_el", float(self.rotor_location[1]))
                            )
                            self.radio_queue.put(("glat", g_lat))
                            self.radio_queue.put(("glon", g_lon))
                        sleep(0.5)
                else:
                    past_rotor_location = self.rotor_location
                    self.rotor_location = self.rotor.get_azimuth_elevation()
                    if not self.rotor_location == past_rotor_location:
                        g_lat, g_lon = self.ephemeris_tracker.convert_to_gal_coord(
                            self.rotor_location
                        )
                        self.radio_queue.put(
                            ("motor_az", float(self.rotor_location[0]))
                        )
                        self.radio_queue.put(
                            ("motor_el", float(self.rotor_location[1]))
                        )
                        self.radio_queue.put(("glat", g_lat))
                        self.radio_queue.put(("glon", g_lon))

                    sleep(1)
            except AssertionError as e:
                self.log_message(str(e))
            except ValueError as e:
                self.log_message(str(e))

    def update_status(self):
        """Periodically Publishes Daemon Status for Dashboard (or any other subscriber)

        Is Operated as an Infinite Looping Thread Function

        Returns
        -------
        None
        """
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
                "vlsr": self.current_vlsr,
                "object_locs": self.ephemeris_locations,
                "az_limits": self.az_limits,
                "el_limits": self.el_limits,
                "stow_loc": self.stow_location,
                "cal_loc": self.cal_location,
                "horizon_points": self.horizon_points,
                "center_frequency": self.radio_center_frequency,
                "frequency_correction": self.radio_frequency_correction,
                "bandwidth": self.radio_sample_frequency,
                "motor_offsets": self.rotor_offsets,
                "queued_item": self.current_queue_item,
                "queue_size": self.command_queue.qsize(),
                "emergency_contact": self.contact,
                "error_logs": self.command_error_logs,
                "temp_cal": self.temp_cal,
                "temp_sys": self.temp_sys,
                "cal_power": self.cal_power,
                "n_point_data": self.n_point_data,
                "rotor_loc_npoint_live": self.rotor_loc_npoint_live,
                "beam_switch_data": self.beam_switch_data,
                "minimal_arrows_distance": self.minimal_arrows_distance,
                "npoint_arrows": self.npoint_arrows,
                "motor_type": self.motor_type,
                "radio_save_task": str(self.radio_save_task),
                "waterfall_length": self.waterfall_length,
                "gui_timezone": self.gui_timezone,
                "display_lim": self.display_lim,
                "station" : self.station,
                "draw_ecliptic" : self.draw_ecliptic,
                "draw_equator" : self.draw_equator,
                "time": time(),
            }
            status_socket.send_json(status)
            sleep(0.5)

    def update_radio_settings(self):
        """Coordinates Sending XMLRPC Commands to the GNU Radio Script

        Is Operated as an Infinite Looping Thread Function

        Returns
        -------
        None
        """
        rpc_server = ServerProxy("http://localhost:5557/")
        while True:
            method, value = self.radio_queue.get()
            call = getattr(rpc_server, f"set_{method}")
            call(value)
            sleep(0.1)

    def update_command_queue(self):
        """Waits for New Commands Coming in Over ZMQ PUSH/PULL

        Is Operated as an Infinite Looping Thread Function

        Returns
        -------
        None
        """
        context = zmq.Context()
        command_port = 5556
        command_socket = context.socket(zmq.PULL)
        command_socket.bind("tcp://*:%s" % command_port)
        while True:
            cmd = command_socket.recv_string()
            self.command_queue.put(cmd)

    def srt_daemon_main(self):
        """Starts and Processes Commands for the SRT

        Returns
        -------
        None
        """

        # Create Infinite Looping Threads
        ephemeris_tracker_thread = Thread(
            target=self.update_ephemeris_location, daemon=True
        )
        rotor_pointing_thread = Thread(target=self.update_rotor_status, daemon=True)
        command_queueing_thread = Thread(target=self.update_command_queue, daemon=True)
        status_thread = Thread(target=self.update_status, daemon=True)
        radio_thread = Thread(target=self.update_radio_settings, daemon=True)

        # If the GNU Radio Script Should be Running, Start It
        if self.radio_autostart:
            try:
                self.radio_process_task.start()
            except RuntimeError as e:
                self.log_message(str(e))
            sleep(5)

        # Send Settings to the GNU Radio Script
        radio_params = {
            "Frequency": (
                "freq",
                self.radio_center_frequency + self.radio_frequency_correction,
            ),
            "Sample Rate": ("samp_rate", self.radio_sample_frequency),
            "Motor Azimuth": ("motor_az", self.rotor_location[0]),
            "Motor Elevation": ("motor_el", self.rotor_location[1]),
            "Motor GalLat": (
                "glat",
                self.ephemeris_tracker.convert_to_gal_coord(self.rotor_location)[0],
            ),
            "Motor GalLon": (
                "glon",
                self.ephemeris_tracker.convert_to_gal_coord(self.rotor_location)[1],
            ),
            "Object Tracking": ("soutrack", "at_stow"),
            "System Temp": ("tsys", self.temp_sys),
            "Calibration Temp": ("tcal", self.temp_cal),
            "Calibration Power": ("cal_pwr", self.cal_power),
            "Calibration Values": ("cal_values", self.cal_values),
            "Is Running": ("is_running", True),
        }
        for name in radio_params:
            self.log_message(f"Setting {name}")
            self.radio_queue.put(radio_params[name])

        # Start Infinite Looping Update Threads
        ephemeris_tracker_thread.start()
        rotor_pointing_thread.start()
        command_queueing_thread.start()
        status_thread.start()
        radio_thread.start()

        while self.keep_running:
            try:
                # Await Command for the SRT
                self.current_queue_item = "None"
                command = self.command_queue.get()
                # Make n-point scan markers disappear on next command
                if (command != "None"):
                    self.rotor_loc_npoint_live = []
                self.log_message(f"Running Command '{command}'")
                self.current_queue_item = command
                if len(command) < 2 or command[0] == "*":
                    continue
                elif command[0] == ":":
                    command = command[1:].strip()
                command_parts = command.split(" ")
                command_parts = [x for x in command_parts if x]
                command_name = command_parts[0].lower()

                # If Command Starts With a Valid Object Name
                if command_parts[0] in self.ephemeris_locations:
                    if command_parts[-1] == "n":  # N-Point Scan About Object
                        self.n_point_scan(self.n_pnt_count, object_id=command_parts[0])
                    elif command_parts[-1] == "b":  # Beam-Switch Away From Object
                        self.beam_switch(object_id=command_parts[0])
                    else:  # Point Directly At Object
                        self.point_at_object(object_id=command_parts[0])
                elif command_name == "stow":
                    self.stow()
                elif command_name == "cal":
                    self.point_at_azel(*self.cal_location)
                elif command_name == "calibrate":
                    self.calibrate()
                elif command_name == "quit":
                    self.quit()
                elif command_name == "playsound":
                    self.play_sound(command=command)
                elif command_name == "record":
                    self.start_recording(
                        name=(None if len(command_parts) <= 1 else command_parts[1])
                    )
                elif command_name == "roff":
                    self.stop_recording()
                elif command_name == "freq":
                    self.set_freq(frequency=float(command_parts[1]) * pow(10, 6))
                elif command_name == "samp":
                    self.set_samp_rate(samp_rate=float(command_parts[1]) * pow(10, 6))
                elif command_name == "azel":
                    self.point_at_azel(
                        float(command_parts[1]),
                        float(command_parts[2]),
                    )
                elif command_name == "offset":
                    self.point_at_offset(
                        float(command_parts[1]), float(command_parts[2])
                    )
                elif (
                    command_name.isnumeric()
                ):  # If Command is a Number, Sleep that Long
                    sleep(float(command_name))
                elif command_name == "wait":
                    sleep(float(command_parts[1]))
                elif command_name.split(":")[0] == "lst":  # Wait Until Next Time H:M:S
                    time_string = command_name.replace("LST:", "")
                    time_val = datetime.strptime(time_string, "%H:%M:%S")
                    while time_val < datetime.fromtimestamp(time(), timezone.utc):
                        time_val += timedelta(days=1)
                    time_delta = (
                        time_val - datetime.fromtimestamp(time(), timezone.utc)
                    ).total_seconds()
                    sleep(time_delta)
                elif len(command_name.split(":")) == 5:  # Wait Until Y:D:H:M:S
                    time_val = datetime.strptime(command_name, "%Y:%j:%H:%M:%S")
                    time_delta = (
                        time_val - datetime.fromtimestamp(time(), timezone.utc)
                    ).total_seconds()
                    sleep(time_delta)
                else:
                    self.log_message(f"Command Not Identified '{command}'")
                self.command_queue.task_done()
            except IndexError as e:
                self.log_message(str(e))
            except ValueError as e:
                self.log_message(str(e))
            except ConnectionRefusedError as e:
                self.log_message(str(e))

        # On End, Return to Stow and End Recordings
        self.stop_recording()
        self.stow()
        if self.radio_autostart:
            sleep(1)
            self.radio_process_task.terminate()
