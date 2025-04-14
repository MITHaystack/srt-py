"""object_tracker.py

Module for Tracking and Caching the Azimuth-Elevation Coords of Celestial Objects

"""
from astropy.coordinates import SkyCoord, EarthLocation, get_body #get_sun, get_moon
from astropy.coordinates import ICRS, Galactic, FK4, CIRS, AltAz, LSR
from astropy.utils.iers.iers import conf
from astropy.table import Table
from astropy.time import Time
import astropy.units as u

import numpy as np
from pathlib import Path
from copy import deepcopy


root_folder = Path(__file__).parent.parent.parent.parent


class EphemerisTracker:
    """
    Enables Calculating the AzEl Coordinates of the Bodies Specified in sky_coords.csv
    """

    def __init__(
        self,
        observer_lat,
        observer_lon,
        observer_elevation=0,
        config_file="config/sky_coords.csv",
        refresh_time=10,
        auto_download=True,
    ):
        """Initializer for EphemerisTracker

        - Reads CSV File for Objects to Track
        - Converts to Common Coordinate System
        - Populates AzEl Dictionary with Current Values

        Parameters
        ----------
        observer_lat : float
            Observer's Location Latitude in degrees
        observer_lon : float
            Observer's Location Longitude in degrees
        observer_elevation : float
            Observer's Location Elevation in meters
        config_file : str
            Location of the List File for Bodies Being Tracked
        refresh_time : float
            Maximum Amount of Time Cache is Valid
        auto_download : bool
            Whether AstroPy is Permitted to Use Internet to Increase Accuracy
        """

        table = Table.read(Path(root_folder, config_file), format="ascii.csv")

        self.sky_coord_names = {}
        sky_coords_ra = np.zeros(len(table))
        sky_coords_dec = np.zeros(len(table))


        for index, row in enumerate(table):
            coordinate_system = row["coordinate_system"]
            coordinate_a = row["coordinate_a"]
            coordinate_b = row["coordinate_b"]
            name = row["name"]
            unit = (
                u.deg
                if coordinate_system == Galactic.__name__.lower()
                else (u.hourangle, u.deg)
            )
            sky_coord = SkyCoord(
                coordinate_a, coordinate_b, frame=coordinate_system, unit=unit
            )
            sky_coord_transformed = sky_coord.transform_to(CIRS)
            sky_coords_ra[index] = sky_coord_transformed.ra.degree
            sky_coords_dec[index] = sky_coord_transformed.dec.degree
            self.sky_coord_names[name] = index

        self.location = EarthLocation.from_geodetic(
            lat=observer_lat * u.deg,
            lon=observer_lon * u.deg,
            height=observer_elevation * u.m,
        )

        self.sky_coords = SkyCoord(
            ra=sky_coords_ra * u.deg, dec=sky_coords_dec * u.deg, frame=CIRS, location=self.location)

        self.bodies = ["Sun", "Moon", "Jupiter"] #list bodies we want to track so other functions can grab these (really should pull in from config file)
        ##variable to hold a target skycoord object

        self.target = SkyCoord(ra= 0*u.deg, dec= 0*u.deg,frame='icrs', location=self.location)


        self.latest_time = None
        self.refresh_time = refresh_time * u.second

        self.az_el_dict = {}
        self.target_coords =(0,0) #separate thing just to store target to so we don't display the point in the gui
        # self.vlsr_dict = {}
        # self.time_interval_dict = {}
        self.time_interval_dict = self.inital_azeltime()

        self.update_all_az_el()

        # self.update_azeltime()
        conf.auto_download = auto_download


    def calculate_az_el(self, name, time, alt_az_frame):
        """Calculates Azimuth and Elevation of the Specified Object at the Specified Time

        Parameters
        ----------
        name : str
            Name of the Object being Tracked
        time : Time
            Current Time (only necessary for Sun/Moon Ephemeris)
        alt_az_frame : AltAz
            AltAz Frame Object

        Returns
        -------
        (float, float)
            (az, el) Tuple
        """
        if (name == "Sun") or (name =="Moon"):
            alt_az = get_body(time=time, body=name,location=self.location).transform_to(alt_az_frame)
        else:
            alt_az = self.sky_coords[self.sky_coord_names[name]].transform_to(
                alt_az_frame
            )
        return alt_az.az.degree, alt_az.alt.degree



    def calculate_vlsr(self, sky_coord, time):

        """
        Calculates observer velocity correction in the local standard of rest 
        (e.g. relative to galactic center) along telescope line of sight.
        Note we do not actuially care about the details of the object and are not attempting to 
        correct for target motion. We only care about where we are pointing.

        Parameters
        ----------
        sky_coord : SkyCoord
            Sky cordinate object
            note: must contain location attribute
        time : Time
            Time for conversion
        """
            
        #cast anything into icrs to make life easy (note this means AltAz frames must contain a time)
        sky_coord_radec = sky_coord.transform_to('icrs')
        
        #barycentric correction
        v_bary = sky_coord_radec.radial_velocity_correction(obstime=time)

        sky_coord_no_vel = ICRS(ra=sky_coord_radec.ra.deg*u.deg, dec=sky_coord_radec.dec.deg*u.deg, 
                pm_ra_cosdec=0*u.mas/u.yr, pm_dec=0*u.mas/u.yr, 
                radial_velocity=0*u.km/u.yr, distance = 10*u.pc)
        #solar motion wrt galactic center
        v_sun = sky_coord_no_vel.transform_to(LSR()).radial_velocity
        
        return (v_bary+v_sun).to(u.km/u.s).value

        
    def convert_to_gal_coord(self, az_el, time=None):
        """Converts an AzEl Tuple into a Galactic Tuple from Location

        Parameters
        ----------
        az_el : (float, float)
            Azimuth and Elevation to Convert
        time : AstroPy Time Obj
            Time of Conversion

        Returns
        -------
        (float, float)
            Galactic Latitude and Longitude
        """
        if time is None:
            time = Time.now()
        az, el = az_el
        start_frame = AltAz(
            obstime=time, location=self.location, alt=el * u.deg, az=az * u.deg
        )
        end_frame = Galactic()
        result = start_frame.transform_to(end_frame)
        g_lat = float(result.b.degree)
        g_lng = float(result.l.degree)
        return g_lat, g_lng

    def update_all_az_el(self):
        """Updates Every Entry in the AzEl Dictionary Cache, if the Cache is Outdated

        Returns
        -------
        None
        """
        if (self.latest_time is not None
            and Time.now() < self.latest_time + self.refresh_time):
            return

        time = Time.now()
        frame = AltAz(obstime=time, location=self.location)
        transformed = self.sky_coords.transform_to(frame)

        for name in self.sky_coord_names:
            index = self.sky_coord_names[name]
            self.az_el_dict[name] = (
                transformed.az[index].degree,
                transformed.alt[index].degree,
            )
            #vlsr = self.calculate_vlsr(transformed[index], time)
            #self.vlsr_dict[name] = vlsr

        #deal with annoying things that move against the sky

        for body in self.bodies:
            body_coords = get_body(time=time, body=body,location=self.location).transform_to(frame)
            self.az_el_dict[body] = (body_coords.az.degree, body_coords.alt.degree)
            #self.vlsr_dict[body] = self.calculate_vlsr(body_coords, time)

        #and prepredict things (do we actually need this?)

        for time_passed in range(0, 61, 5):

            timenew = time + time_passed
            frame = AltAz(obstime=timenew, location=self.location)
            transformed = self.sky_coords.transform_to(frame)

            for name in self.sky_coord_names:
                index = self.sky_coord_names[name]
                self.time_interval_dict[time_passed][name] = (
                    transformed.az[index].degree,
                    transformed.alt[index].degree,
                )

            for body in self.bodies:
                body_coords = get_body(time=time, body=body,location=self.location).transform_to(frame)
                self.time_interval_dict[time_passed][body] = (body_coords.az.degree, body_coords.alt.degree)

        self.latest_time = time

    def update_track(self, object_id):

        time = Time.now()
        frame = AltAz(obstime=time, location=self.location)

        if object_id == "target":
            transformed = self.target.transform_to(frame)
            self.target_coords = (
                transformed.az.degree,
                transformed.alt.degree
            )

        elif object_id in self.sky_coord_names: #then this is a normal programmed object and we'll just rerun the usual calculation only for that point
            index = self.sky_coord_names[object_id]
            transformed = self.sky_coords[index].transform_to(frame) 
            self.target_coords = (
                transformed.az.degree,
                transformed.alt.degree
            )

        elif object_id in self.bodies: #annoying things like planets
            body_coords = get_body(time=time, body=object_id,location=self.location).transform_to(frame)
            self.target_coords = (body_coords.az.degree, body_coords.alt.degree)

        else:
            return

    def get_track_azimuth_elevation(self,object_id): #for tracking updates

            return self.target_coords 


    def get_all_azimuth_elevation(self):
        """Returns Dictionary Mapping the Objects to their Current AzEl Coordinates

        Returns
        -------
        self.az_el_dict : {str: (float, float)}
        """
        return self.az_el_dict

    def get_all_azel_time(self):
        """Returns Dictionary Mapping the Time Offset to a dictionary of updated azel coordinates

        Returns
        -------
        self.time_interval_dict : {int: {str: (float, float)}}s
        """
        # return
        return self.time_interval_dict

    # def get_azimuth_elevation(self, name, time_offset):
    #     """Returns Individual Object AzEl at Specified Time Offset

    #     Parameters
    #     ----------
    #     name : str
    #         Object Name
    #     time_offset : Time
    #         Any Offset from the Current Time
    #     Returns
    #     -------
    #     (float, float)
    #         (az, el) Tuple
    #     """
    #     if time_offset == 0:
    #         return self.get_all_azimuth_elevation()[name]
    #     else:
    #         time = Time.now() + time_offset
    #         return self.calculate_az_el(
    #             name, time, AltAz(obstime=time, location=self.location)
    #         )

    #def get_all_vlsr(self):
    #    return self.vlsr_dict

    # def get_vlsr(self, name, time_offset=0): #not used

    #     if time_offset == 0:
    #         return self.get_all_vlsr()[name]
    #     else:
    #         time = Time.now() + time_offset
    #         frame = AltAz(obstime=time, location=self.location)
    #         return self.calculate_object_vlsr(name, time, frame)

    def inital_azeltime(self):
        new_dict = {}
        for time_passed in range(0, 61, 5):
            # new_time_dict = deepcopy(self.az_el_dict)
            new_time_dict = {}
            new_dict[time_passed] = new_time_dict
        return new_dict

    def update_azeltime(self):
        # if (
        #     self.latest_time is not None
        #     and Time.now() < self.latest_time + self.refresh_time
        # ):
        #     return

        for time_passed in range(0, 61, 5):

            time = Time.now() + time_passed
            frame = AltAz(obstime=time, location=self.location)
            transformed = self.sky_coords.transform_to(frame)

            for name in self.sky_coord_names:
                index = self.sky_coord_names[name]
                self.time_interval_dict[time_passed][name] = (
                    transformed.az[index].degree,
                    transformed.alt[index].degree,
                )
        self.latest_time = Time.now()
        return
