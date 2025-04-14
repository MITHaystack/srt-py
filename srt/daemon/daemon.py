"""daemon.py

Main Control and Orchestration Class for the Small Radio Telescope

"""

from time import sleep, time
from datetime import timedelta, datetime
from threading import Thread
from queue import Queue
from xmlrpc.client import ServerProxy
from pathlib import Path
from operator import add
import os

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
from .utilities.functions import azel_within_range, get_spectrum
from .utilities.calibration_functions import basic_cold_sky_calibration_fit, additive_noise_calibration_fit

#pull astropy things into the daemon too for now so we can create skycoord objects here more easily

from astropy.coordinates import SkyCoord, EarthLocation
from astropy.coordinates import ICRS, Galactic, FK4, CIRS, AltAz, LSR
from astropy.utils.iers.iers import conf
from astropy.table import Table
from astropy.time import Time
import astropy.units as u

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
        print(config_dict)
        self.config_directory = config_directory
        if "STATION" in config_dict:
            self.station = config_dict["STATION"]
        else:
            self.station = {"latitude": 0.0,
                            "longitude": 0.0,
                            "name": None}
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
        self.radio_rf_gain = config_dict["RADIO_RF_GAIN"]
        self.radio_frequency_correction = config_dict["RADIO_FREQ_CORR"]
        self.radio_num_bins = config_dict["RADIO_NUM_BINS"]
        self.radio_integ_cycles = config_dict["RADIO_INTEG_CYCLES"]
        self.radio_autostart = config_dict["RADIO_AUTOSTART"]
        self.num_beamswitches = config_dict["NUM_BEAMSWITCHES"]
        self.beamwidth = config_dict["BEAMWIDTH"]
        self.cal_type = config_dict["CAL_TYPE"]
        self.cal_cycles = config_dict["CAL_INTEGRATION_CYCLES"]
        self.temp_sys = config_dict["TSYS"]
        self.temp_cal = config_dict["TCAL"]
        self.save_dir = config_dict["SAVE_DIRECTORY"]
        self.dashboard_refresh_rate = config_dict["DASHBOARD_REFRESH_MS"]/1000.0
        
        self.npoints = 5 #default size of grid for npoint scan
        self.radio_calibrator_state = False

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
            config_file=str(
                Path(config_directory, "sky_coords.csv").absolute()),
        )
        self.ephemeris_locations = self.ephemeris_tracker.get_all_azimuth_elevation()
        self.ephemeris_time_locs = self.ephemeris_tracker.get_all_azel_time()
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

        #vars pulled in from rotor definition
        #self.rotor.rotor_loop_cadence
        #self.rotor.pointing_accuracy

        print("test", self.stow_location)
        self.rotor_location = (0,0)#self.stow_location
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
        self.command_error_logs.append((time(), message))
        print(message)

    def n_point_scan(self, object_id, grid_size=5):
        """Runs an N-Point (25) Scan About an Object

        Parameters
        ----------
        object_id : str
            Name of the Object to Perform N-Point Scan About

        Returns
        -------
        None
        """
        self.ephemeris_cmd_location = None
        self.radio_queue.put(("soutrack", object_id))

        scan_center = self.ephemeris_locations[object_id]
        self.ephemeris_cmd_location = object_id #tell tracking process to follow scan center

        # Send vlsr to radio queue
        #cur_vlsr = self.ephemeris_vlsr[object_id]
        #self.radio_queue.put(("vlsr", float(self.current_vlsr)))
        #self.current_vlsr = cur_vlsr
        N_pnt_default = grid_size**2
        rotor_loc = []
        pwr_list = []
        #
        
        np_sides = [grid_size, grid_size]
        for scan in range(N_pnt_default):
            scan_center = self.ephemeris_locations[object_id] #recompute target position for every iteration
            self.log_message("{0} of {1} point scan.".format(scan, N_pnt_default))
            i = (scan // grid_size) - int(grid_size/2)
            j = (scan % grid_size) - int(grid_size/2)
            el_dif = i * self.beamwidth * 0.5
            az_dif_scalar = np.cos((scan_center[1] + el_dif) * np.pi / 180.0)
            # Avoid issues where you get close to the zenith
            if np.abs(az_dif_scalar) < 1e-4:
                az_dif = 0
            else:
                az_dif = j * self.beamwidth * 0.5 / az_dif_scalar

            new_rotor_offsets = (az_dif, el_dif)

            if self.rotor.angles_within_bounds(*scan_center):
                #self.rotor_destination = self.ephemeris_locations[object_id] #this line is probably redundant
                self.point_at_offset(*new_rotor_offsets)
            rotor_loc.append(self.rotor_location)
            sleep(5)
            raw_spec = get_spectrum(port=5561)
            p = np.sum(raw_spec)
            a = len(raw_spec)
            pwr = (self.temp_sys + self.temp_cal) * p / (a * self.cal_power)
            pwr_list.append(pwr)
        maxdiff = (az_dif, el_dif)
        self.n_point_data = [scan_center, maxdiff,
                             rotor_loc, pwr_list, np_sides]

        # add code to collect spectrum data.
        self.rotor_offsets = (0.0, 0.0)
        self.ephemeris_cmd_location = object_id

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

        new_rotor_destination = self.ephemeris_locations[object_id]
        rotor_loc = []
        pwr_list = []
        for j in range(0, 3 * self.num_beamswitches):
            new_rotor_destination = self.ephemeris_locations[object_id] #recompute target position for every iteration
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
       
        new_rotor_cmd_location = self.ephemeris_locations[object_id]
        if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
            self.ephemeris_cmd_location = object_id
            self.rotor_destination = new_rotor_cmd_location
            self.rotor_cmd_location = new_rotor_cmd_location
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location, bounds=(self.rotor.pointing_accuracy,self.rotor.pointing_accuracy)):
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

        #define a skycoord object with az el position info

        #obstime = Time.now()

        #sky_coord = SkyCoord(AltAz(obstime=obstime, location=self.ephemeris_tracker.location, alt=el * u.deg, az=az * u.deg))
        #self.ephemeris_tracker.target=sky_coord

        if self.ephemeris_cmd_location is not None:
            self.ephemeris_cmd_location = None #clear tracking command
            sleep(0.05) #give the ephemeris tracker time to finish and stop causing trouble

        self.rotor_offsets = (0.0, 0.0)
        # Send az and el angles to sources track for the radio
        self.radio_queue.put(("soutrack", f"azel_{az}_{el}"))

        new_rotor_destination = (az, el)
        new_rotor_cmd_location = new_rotor_destination
        if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
            self.rotor_destination = new_rotor_destination
            self.rotor_cmd_location = new_rotor_cmd_location
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location, bounds=(self.rotor.pointing_accuracy,self.rotor.pointing_accuracy)):
                self.rotor_destination = new_rotor_destination
                self.rotor_cmd_location = new_rotor_cmd_location
                sleep(0.1)
        else:

            self.log_message(f"Object at {new_rotor_cmd_location} Not in Motor Bounds")
            
    def point_at_galactic(self, l_pos, b_pos):
        """Points Antenna at a Specific Galactic longitude and lattitude

        Parameters
        ----------
        l_pos : float
            longitude, in degrees, to turn antenna towards
        b_pos : float
            lattitude, in degrees, to point antenna upwards at
        duration : float
            duration in seconds to continue tracking coordinate
            
        Returns
        -------
        None
        """   

        #clear preexisting track (prevents target update collisions)
        self.ephemeris_cmd_location = None 

        #define a skycoord object with galactic coord info

        sky_coord = SkyCoord(l_pos, b_pos, frame='galactic', unit=u.deg, location=self.ephemeris_tracker.location)
        self.ephemeris_tracker.target=sky_coord
        object_id = "target"
        sleep(0.05)

        
        #if (self.motor_type == "W1XM_BIG_DISH"):
            #rotor is smart enough to directly handle the command, need to eventually restructure so we can pass it nicely

        #    self.log_message("direct galactic coordinate commands not yet supported for your rotor. using standard tracking") 
        #else:
            #rotor needs command converted to az-el
        #    self.log_message("direct galactic coordinate commands not yet supported for your rotor. using standard tracking")

        self.rotor_offsets = (0.0, 0.0)
        self.radio_queue.put(("soutrack", f"radec_{l_pos}_{b_pos}"))

        azel_frame = AltAz(obstime=Time.now(), location=self.ephemeris_tracker.location, alt=self.rotor_location[1] * u.deg, az=self.rotor_location[0] * u.deg)
        target_azel = sky_coord.transform_to(azel_frame)
        new_rotor_destination = (target_azel.az.degree, target_azel.alt.degree)
        new_rotor_cmd_location = tuple(map(add, new_rotor_destination, self.rotor_offsets))
        
        if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
            self.ephemeris_cmd_location = object_id
            self.rotor_destination = new_rotor_cmd_location
            self.rotor_cmd_location = new_rotor_cmd_location
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location, bounds=(self.rotor.pointing_accuracy,self.rotor.pointing_accuracy)):
                sleep(0.1)
        else:
            self.log_message(f"Object {object_id} Not in Motor Bounds")
            self.ephemeris_cmd_location = None
    
    def point_at_radec(self, ra_pos, dec_pos):
        """Points Antenna at a specific ICRS coordinate in Ra Dec 
        (Bigdish uses J2000)

        Parameters
        ----------
        ra_pos : float
            right ascension, in degrees, to turn antenna towards
        dec_pos : float
            declination, in degrees, to point antenna upwards at
        duration : float
            duration in seconds to continue tracking coordinate
            
        Returns
        -------
        None
        """

        #clear preexisting track (prevents target update collisions)
        self.ephemeris_cmd_location = None

        sky_coord = SkyCoord(ra_pos, dec_pos, frame='icrs', unit=u.deg, location=self.ephemeris_tracker.location)
        self.ephemeris_tracker.target=sky_coord
        object_id = "target" 

        self.rotor_offsets = (0.0, 0.0)
        self.radio_queue.put(("soutrack", f"radec_{ra_pos}_{dec_pos}"))

        azel_frame = AltAz(obstime=Time.now(), location=self.ephemeris_tracker.location, alt=self.rotor_location[1] * u.deg, az=self.rotor_location[0] * u.deg)
        target_azel = sky_coord.transform_to(azel_frame)
        new_rotor_destination = (target_azel.az.degree, target_azel.alt.degree)
        new_rotor_cmd_location = tuple(map(add, new_rotor_destination, self.rotor_offsets))

        if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
            self.ephemeris_cmd_location = object_id
            self.rotor_destination = new_rotor_cmd_location
            self.rotor_cmd_location = new_rotor_cmd_location
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location, bounds=(self.rotor.pointing_accuracy,self.rotor.pointing_accuracy)):
                sleep(0.1)
        else:
            self.log_message(f"Object {object_id} Not in Motor Bounds")
            self.ephemeris_cmd_location = None      

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
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location, bounds=(self.rotor.pointing_accuracy,self.rotor.pointing_accuracy)):
                sleep(0.1)
        else:
            self.log_message(f"Offset {new_rotor_offsets} Out of Bounds")

    def stow(self):
        """Moves the Antenna Back to its Stow Location

        Returns
        -------
        None
        """

        self.point_at_azel(self.stow_location[0], self.stow_location[1])
        
        #self.ephemeris_cmd_location = None
        #self.radio_queue.put(("soutrack", "at_stow"))
        #self.rotor_offsets = (0.0, 0.0)
        #self.rotor_destination = self.stow_location
        #self.rotor_cmd_location = self.stow_location
        #while not azel_within_range(self.rotor_location, self.rotor_cmd_location):
        #    sleep(0.1)

    def calibrate(self):
        """Runs Calibration Processing and Pushes New Values to Processing Script

        Returns
        -------
        None
        """

        #kill any running file save operations since we're about to scramble them

        if self.radio_save_task is not None:
            self.radio_save_task.terminate()
        
        # erase existing calibration
        self.cal_values = [1.0 for _ in range(self.radio_num_bins)]
        self.cal_power = 1.0
        
        self.radio_queue.put(("cal_pwr", self.cal_power))
        self.radio_queue.put(("cal_values", self.cal_values))

        '''
        simple cold sky cal for the basic SRT
        '''

        if self.cal_type == "COLD_SKY":
            #define filenames for calibration measurements
            cold_sky_name = "cold_sky.fits"

            #erase prior calibration files if present
            cold_sky_file=str(Path(self.config_directory, cold_sky_name).absolute())
            if os.path.exists(cold_sky_file):
                os.remove(cold_sky_file)

            self.log_message("Starting cold calibration reference measurement")

            #start saving new calibration file
            sleep(0.1+2*self.radio_num_bins * self.radio_integ_cycles / self.radio_sample_frequency)
            self.start_recording(name=cold_sky_name, file_dir=self.config_directory)
            sleep((self.cal_cycles+1)*self.radio_num_bins* self.radio_integ_cycles/ self.radio_sample_frequency)
            self.stop_recording()

            
            ### compute calibration corrections

            cal_values, cal_power = basic_cold_sky_calibration_fit(cold_sky_file, self.temp_sys, self.temp_cal, 20)




        '''
        if we have a noise diode to use for calibration we need to make multiple measurements
        '''

        if self.cal_type == "NOISE_DIODE":
            #define filenames for calibration measurements
            cold_sky_name = "cold_sky.fits"
            cal_ref_name = "cold_sky_plus_cal.fits"

            #erase prior calibration files if present
            cold_sky_file=str(Path(self.config_directory, cold_sky_name).absolute())
            cal_ref_file=str(Path(self.config_directory, cal_ref_name).absolute())

            if os.path.exists(cold_sky_file):
                os.remove(cold_sky_file)

            if os.path.exists(cal_ref_file):
                os.remove(cal_ref_file)

            #enable calibrator and wait for the idiotically long settling time the filters currently have 
            #(need to fix that eventually so integration intervals are fully independent like they should be)

            self.log_message("Starting hot calibration reference measurement")

            self.set_calibrator_state(True)
            sleep(0.1+2*self.radio_num_bins * self.radio_integ_cycles / self.radio_sample_frequency)
            self.start_recording(name=cal_ref_name, file_dir=self.config_directory)
            sleep((self.cal_cycles+1)*self.radio_num_bins* self.radio_integ_cycles/ self.radio_sample_frequency)
            self.stop_recording()

            #disable calibrator and wait for the idiotically long settling time the filters currently have 
            #(need to fix that eventually so integration intervals are fully independent like they should be)

            self.log_message("Starting cold calibration reference measurement")

            self.set_calibrator_state(False)
            sleep(0.1+2*self.radio_num_bins * self.radio_integ_cycles / self.radio_sample_frequency)
            self.start_recording(name=cold_sky_name, file_dir=self.config_directory)
            sleep((self.cal_cycles+1)*self.radio_num_bins* self.radio_integ_cycles/ self.radio_sample_frequency)
            self.stop_recording()

            cal_values, cal_power = additive_noise_calibration_fit(cold_sky_file, cal_ref_file, self.temp_sys, self.temp_cal, 20)


        #erase old cal file to prevent wierdness

        calibration_path = Path(self.config_directory, "calibration.json")
        if os.path.exists(calibration_path):
                os.remove(calibration_path)

        #save result

        file_output = {
            "cal_pwr": cal_power,
            "cal_values": cal_values.tolist(),
        }
        with open(calibration_path, "w") as outfile:
            json.dump(file_output, outfile)

        #write corrections back to processing

        #readback from file is to circumvent a wierd formatting issue I can't figure out

        sleep(0.1)
        path = Path(self.config_directory, "calibration.json")
        with open(path, "r") as input_file:
            cal_data = json.load(input_file)
            self.cal_values = cal_data["cal_values"]
            self.cal_power = cal_data["cal_pwr"]
        self.radio_queue.put(("cal_pwr", self.cal_power))
        self.radio_queue.put(("cal_values", self.cal_values))
    

        self.log_message("Calibration Done")

    def start_recording(self, name, file_dir):
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
                    self.radio_sample_frequency, file_dir, name
                )
            elif name.endswith(".rad"):
                name = None if name == "*.rad" else name
                self.radio_save_task = RadioSaveSpecRadTask(
                    self.radio_sample_frequency,
                    self.radio_num_bins,
                    file_dir,
                    name,
                )
            elif name.endswith(".fits"):
                name = None if name == "*.fits" else name
                self.radio_save_task = RadioSaveSpecFitsTask(
                    self.radio_sample_frequency,
                    self.radio_num_bins,
                    file_dir,
                    name,
                )
            else:
                self.radio_save_task = RadioSaveRawTask(
                    self.radio_sample_frequency, file_dir, name
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
            
    def set_npoints(self, n):
        """Set the number of points for the N point scan
        
        Parameters
        ----------
        npoints : number of points along grid edge for npoint scan
        """
        self.npoints = n

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

    def set_coords(self, lat, long, config_directory="config/sky_coords.csv", name=None):
        """Set the lat/long coordinates of observer location

        Parameters
        ----------
        lat : float
            Observer Latitude, in degs, to Set SDR to

        long: float
            Observer Longitude, in degs, to Set SDR to

        name: string
            Observer location name, None if not given

        Returns
        -------
        None
        """
        self.station = {"latitude": lat,
                        "longitude": long,
                        "name": name}
        self.ephemeris_tracker = EphemerisTracker(
            self.station["latitude"],
            self.station["longitude"],
            # config_file=str(
            #     Path(config_directory, "sky_coords.csv").absolute()),
        )
        # self.radio_queue.put((""))

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

    def set_rf_gain(self, rf_gain):
        """Set the rf gain of the radio

        Note that this stops any currently running raw saving tasks

        Parameters
        ----------
        rf_gain : float
            rf_gain for the SDR in dB

        Returns
        -------
        None
        """
        if self.radio_save_task is not None:
            self.radio_save_task.terminate()
        #save old gain and cal values
        #old_gain = self.radio_rf_gain 
        #old_cal_values = self.cal_values
        
        self.radio_rf_gain = rf_gain
        #self.cal_values = old_cal_values* 10**(0.1*(old_gain - self.radio_rf_gain))
        
        self.radio_queue.put(("rf_gain", self.radio_rf_gain))
        #self.radio_queue.put(("cal_values", self.cal_values))
        
    def set_calibrator_state(self, calibrator_state):
        """Set the state of the calibrator via radio GPIO

        Note that this is highly system specific and must be programmed appropriately

        Parameters
        ----------
        calibrator_state : boolean
            whether the calibrator is on

        Returns
        -------
        None
        """
        if self.cal_type == "NOISE_DIODE":
            #customize for appropriate control scheme
            self.radio_calibrator_state = calibrator_state
            self.radio_queue.put(("cal_on", self.radio_calibrator_state))
            #sleep(0.1)
            
        else:
            self.log_message("Noise Source Not Implemented")
    

    def quit(self):
        """Stops the Daemon Process

        Returns
        -------
        None
        """
        self.keep_running = False
        self.radio_queue.put(("is_running", self.keep_running))

    def find_object_location(self, name):
        """Get azel location of given object and sets as rotor location. 

        Returns
        -------
        None
        """
        if name in self.ephemeris_tracker.az_el_dict:
            az, el = self.ephemeris_tracker.az_el_dict[name][0], self.ephemeris_tracker.az_el_dict[name][1]
            self.log_message(f"here {az,el}")

        self.rotor_location = (az, el)

        self.rotor_offsets = (0.0, 0.0)

        new_rotor_cmd_location = (az, el)
        if self.rotor.angles_within_bounds(*new_rotor_cmd_location):
            self.ephemeris_cmd_location = name
            self.rotor_destination = new_rotor_cmd_location
            self.rotor_cmd_location = new_rotor_cmd_location
            while not azel_within_range(self.rotor_location, self.rotor_cmd_location, bounds=(self.rotor.pointing_accuracy,self.rotor.pointing_accuracy)):
                sleep(0.1)
        else:
            self.log_message(f"Object {name} Not in Motor Bounds")
            self.ephemeris_cmd_location = None

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
                self.ephemeris_locations = (self.ephemeris_tracker.get_all_azimuth_elevation())

                #only update vlsr when we care and only at cadence we update celestial coordinates
                #do this in rotor update loop, not here
                #self.ephemeris_vlsr = self.ephemeris_tracker.get_all_vlsr()

                self.ephemeris_time_locs = (self.ephemeris_tracker.get_all_azel_time())

            #sleep(0.1)

    def update_target_position(self): 
        """Update position of point we are tracking separately from the display ephemeris

        Is Operated as an Infinite Looping Thread Function

        Returns
        -------
        None
        """
        last_updated_time = None
        #last_ephemeris_cmd_location = None
        tracking_update_time = 5


        while True:
            if self.ephemeris_cmd_location is not None:

                if ((last_updated_time is None) or (time() - last_updated_time > tracking_update_time)):
                    #last_ephemeris_cmd_location = self.ephemeris_cmd_location
                    last_updated_time = time()

                    self.ephemeris_tracker.update_track(self.ephemeris_cmd_location)
                    new_rotor_destination = self.ephemeris_tracker.get_track_azimuth_elevation(self.ephemeris_cmd_location)
                    new_rotor_cmd_location = tuple(map(add, new_rotor_destination, self.rotor_offsets))

                    if self.rotor.angles_within_bounds(
                        *new_rotor_destination) and self.rotor.angles_within_bounds(*new_rotor_cmd_location):
                        self.rotor_destination = new_rotor_destination
                        self.rotor_cmd_location = new_rotor_cmd_location

                    else:
                        self.log_message(f"Object {self.ephemeris_cmd_location} moved out of motor bounds")
                        self.ephemeris_cmd_location = None

            sleep(0.1)





    def update_rotor_status(self):
        """Periodically Sets Rotor Azimuth and Elevation and Fetches New Antenna Position

        Is Operated as an Infinite Looping Thread Function

        Returns
        -------
        None

        """

        last_time = time()

        while True:
            
            try:
                current_rotor_cmd_location = self.rotor_cmd_location
                if not azel_within_range(
                    self.rotor_location, current_rotor_cmd_location, bounds=(self.rotor.pointing_accuracy,self.rotor.pointing_accuracy)):

                    self.rotor.set_azimuth_elevation(
                        *current_rotor_cmd_location)
                    
                    sleep(self.rotor.rotor_loop_cadence)
                    start_time = time()
                    while (
                        not azel_within_range(
                            self.rotor_location, current_rotor_cmd_location, bounds=(self.rotor.pointing_accuracy,self.rotor.pointing_accuracy)
                        )
                    ) and (time() - start_time) < 15:
                        past_rotor_location = self.rotor_location
                        self.rotor_location = self.rotor.get_azimuth_elevation()
                        #print(past_rotor_location, self.rotor_location)
                        if not self.rotor_location == past_rotor_location:

                            obstime = Time.now()

                            g_lat, g_lon = self.ephemeris_tracker.convert_to_gal_coord(self.rotor_location)
                            self.radio_queue.put(("motor_az", float(self.rotor_location[0])))
                            self.radio_queue.put(("motor_el", float(self.rotor_location[1])))
                            self.radio_queue.put(("glat", g_lat))
                            self.radio_queue.put(("glon", g_lon))

                            #compute vlsr for where we're actually pointed. we don't really care if it's theoretically different for the target object
                            
                            azel_frame = AltAz(obstime=obstime, location=self.ephemeris_tracker.location, alt=self.rotor_location[1] * u.deg, az=self.rotor_location[0] * u.deg)
                            sky_coord = SkyCoord(azel_frame)
                            self.current_vlsr = self.ephemeris_tracker.calculate_vlsr(sky_coord,obstime)
                            self.radio_queue.put(("vlsr", float(self.current_vlsr)))

                        sleep(self.rotor.rotor_loop_cadence)
                else:

                    if (time() - last_time) > 5 : #don't bother recomputing the celestial coordinates so often if we're not actally moving

                        self.rotor.set_azimuth_elevation(*current_rotor_cmd_location) #always reissue pointing commands periodically and let rotor decide whether to adjust
                        #sleep(0.3) #move this to the pointing routine in motors.py where it belongs

                        past_rotor_location = self.rotor_location
                        self.rotor_location = self.rotor.get_azimuth_elevation()

                        obstime = Time.now()

                        g_lat, g_lon = self.ephemeris_tracker.convert_to_gal_coord(self.rotor_location)
                        self.radio_queue.put(("motor_az", float(self.rotor_location[0])))
                        self.radio_queue.put(("motor_el", float(self.rotor_location[1])))
                        self.radio_queue.put(("glat", g_lat))
                        self.radio_queue.put(("glon", g_lon))

                        #compute vlsr for where we're actually pointed. we don't really care if it's theoretically different for the target object
                                
                        azel_frame = AltAz(obstime=obstime, location=self.ephemeris_tracker.location, alt=self.rotor_location[1] * u.deg, az=self.rotor_location[0] * u.deg)
                        sky_coord = SkyCoord(azel_frame)
                        self.current_vlsr = self.ephemeris_tracker.calculate_vlsr(sky_coord,obstime)
                        self.radio_queue.put(("vlsr", float(self.current_vlsr)))

                        last_time = time()

                    sleep(self.rotor.rotor_loop_cadence) #make it much more responsive to commands
                    #aparrently making this loop too fast causes stability issues. prolly need to tweak rotor level code a bit to not 
                    #crash and burn ir a read comes in before it has a status update request comes before it has new data

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
                "object_time_locs": self.ephemeris_time_locs,
                "az_limits": self.az_limits,
                "el_limits": self.el_limits,
                "stow_loc": self.stow_location,
                "cal_loc": self.cal_location,
                "horizon_points": self.horizon_points,
                "center_frequency": self.radio_center_frequency,
                "rf_gain": self.radio_rf_gain,
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
                "beam_switch_data": self.beam_switch_data,
                "time": time(),
                "cal_state": self.radio_calibrator_state,
            }
            status_socket.send_json(status)
            sleep(self.dashboard_refresh_rate)

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
            sleep(0.01)

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
            target=self.update_ephemeris_location, daemon=True)
        target_tracking_thread = Thread(
            target=self.update_target_position, daemon=True)
        rotor_pointing_thread = Thread(
            target=self.update_rotor_status, daemon=True)
        command_queueing_thread = Thread(
            target=self.update_command_queue, daemon=True)
        status_thread = Thread(target=self.update_status, daemon=True)
        radio_thread = Thread(target=self.update_radio_settings, daemon=True)

        # If the GNU Radio Script Should be Running, Start It
        if self.radio_autostart:
            try:
                self.radio_process_task.start()
            except RuntimeError as e:
                self.log_message(str(e))
            sleep(10) #wait a bit for the radio to actually start up

        # Send Settings to the GNU Radio Script
        radio_params = {
            "Frequency": (
                "freq",
                self.radio_center_frequency + self.radio_frequency_correction,
            ),
            "Sample Rate": ("samp_rate", self.radio_sample_frequency),
            "RF Gain": ("rf_gain", self.radio_rf_gain),
            "Motor Azimuth": ("motor_az", self.rotor_location[0]),
            "Motor Elevation": ("motor_el", self.rotor_location[1]),
            "Motor GalLat": (
                "glat",
                self.ephemeris_tracker.convert_to_gal_coord(
                    self.rotor_location)[0],
            ),
            "Motor GalLon": (
                "glon",
                self.ephemeris_tracker.convert_to_gal_coord(
                    self.rotor_location)[1],
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
        target_tracking_thread.start()
        rotor_pointing_thread.start()
        command_queueing_thread.start()
        status_thread.start()
        radio_thread.start()

        while self.keep_running:
            try:
                # Await Command for the SRT
                self.current_queue_item = "None"
                command = self.command_queue.get()
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
                        self.n_point_scan(object_id=command_parts[0], grid_size=self.npoints)
                    elif command_parts[-1] == "b":  # Beam-Switch Away From Object
                        self.beam_switch(object_id=command_parts[0])
                    else:  # Point Directly At Object
                        self.point_at_object(object_id=command_parts[0])
                elif command_name == "stow":
                    self.stow()
                elif command_name == "cal":
                    self.point_at_azel(*self.cal_location)
                elif command_name == "calon":
                    self.set_calibrator_state(True)
                elif command_name == "caloff":
                    self.set_calibrator_state(False)
                elif command_name == "calibrate":
                    self.calibrate()
                elif command_name == "npointset":
                    self.set_npoints(n=int(command_parts[1]))
                elif command_name == "quit":
                    self.quit()
                elif command_name == "record":
                    self.start_recording(
                        name=(None if len(command_parts) <= 1 else command_parts[1]), file_dir=self.save_dir
                    )
                elif command_name == "roff":
                    self.stop_recording()
                elif command_name == "freq":
                    self.set_freq(frequency=float(
                        command_parts[1]) * pow(10, 6))
                elif command_name == "samp":
                    self.set_samp_rate(samp_rate=float(command_parts[1]) * pow(10, 6))
                elif command_name == "rf_gain":
                    self.set_rf_gain(rf_gain=float(command_parts[1]))
                elif command_name == "coords":
                    self.set_coords(
                        float(command_parts[1]), float(command_parts[2]))
                elif command_name == "object":
                    if command_parts[-1] in self.ephemeris_locations:
                        self.find_object_location(command_parts[-1])
                elif command_name == "obj_coords":
                    self.rotor_location = (
                        float(command_parts[1]), float(command_parts[2]))
                elif command_name == "azel":
                    self.point_at_azel(
                        float(command_parts[1]),
                        float(command_parts[2]),
                    )
                elif command_name == "galactic":
                    self.point_at_galactic(
                        float(command_parts[1]),
                        float(command_parts[2]),
                    )
                elif command_name == "radec":
                    self.point_at_radec(
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
                # Wait Until Next Time H:M:S
                # command format is "wait_utc_hms hour:minute:second" with utc time
                elif command_name == "wait_utc_hms":
                    time_string = command_parts[1]
                    time_val = datetime.strptime(time_string, "%H:%M:%S")
                    while time_val < datetime.utcfromtimestamp(time()):
                        time_val += timedelta(days=1)
                    time_delta = (
                        time_val - datetime.utcfromtimestamp(time())
                    ).total_seconds()
                    self.log_message(f'sleeping for {time_delta} seconds')
                    sleep(time_delta)
                # Wait until next iso time 
                # command format is "wait_utc_iso %Y-%m-%dT%H:%M:%S.%f%z" with utc time
                elif command_name == "wait_utc_iso":
                    time_val = datetime.fromisoformat(
                        command_parts[1])
                    time_delta = (
                        time_val - datetime.utcfromtimestamp(time())
                    ).total_seconds()
                    if time_delta > 0:
                        self.log_message(f'sleeping for {time_delta} seconds')
                        sleep(time_delta)
                    else:
                        self.log_message('target command time past. skipping wait')
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
