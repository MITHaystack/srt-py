from astropy.coordinates import SkyCoord, EarthLocation, get_sun, get_moon
from astropy.coordinates import ICRS, Galactic, FK4, CIRS, AltAz
from astropy.utils.iers.iers import conf
from astropy.table import Table
from astropy.time import Time
import astropy.units as u

import numpy as np


class EphemerisTracker:
    """
    Enables Calculating the AzEl Coordinates of the Bodies Specified in sky_coords.csv
    """

    def __init__(
        self,
        observer_lat,
        observer_lon,
        observer_elevation=0,
        config_file="../config/sky_coords.csv",
        refresh_time=10 * u.second,
        auto_download=True,
    ):
        """
        Initializer for EphemerisTracker
            - Reads CSV File for Objects to Track
            - Converts to Common Coordinate System
            - Populates AzEl Dictionary with Current Values
        :param observer_lat: Observer's Location Latitude in degrees
        :param observer_lon: Observer's Location Longitude in degrees
        :param observer_elevation: Observer's Location Elevation in meters (optional, default=0m)
        :param config_file: Location of the List File for Bodies Being Tracked (optional, default=sky_coords.csv)
        :param refresh_time: Maximum Amount of Time Cache is Valid (optional, default=10s)
        :param auto_download: Whether AstroPy is Permitted to Use Internet to Increase Accuracy (optional, default=True)
        """
        table = Table.read(config_file, format="ascii.csv")

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

        self.sky_coords = SkyCoord(
            ra=sky_coords_ra * u.deg, dec=sky_coords_dec * u.deg, frame=CIRS
        )
        self.location = EarthLocation.from_geodetic(
            lat=observer_lat * u.deg,
            lon=observer_lon * u.deg,
            height=observer_elevation * u.m,
        )
        self.latest_time = Time.now()
        self.refresh_time = refresh_time

        self.az_el_dict = {}
        self.update_all_az_el()
        conf.auto_download = auto_download

    def calculate_az_el(self, name, time, alt_az_frame):
        """
        Calculates Azimuth and Elevation of the Specified Object at the Specified Time
        :param name: Name of the Object being Tracked
        :param time: Current Time (only necessary for Sun/Moon Ephemeris)
        :param alt_az_frame: AltAz Frame Object
        :return: (az, el) Tuple
        """
        if name == "Sun":
            alt_az = get_sun(time).transform_to(alt_az_frame)
        elif name == "Moon":
            alt_az = get_moon(time, self.location).transform_to(alt_az_frame)
        else:
            alt_az = self.sky_coords[self.sky_coord_names[name]].transform_to(
                alt_az_frame
            )
        return alt_az.az.degree, alt_az.alt.degree

    def update_all_az_el(self):
        """
        Updates Every Entry in the AzEl Dictionary Cache, if the Cache is Outdated
        """
        if Time.now() < self.latest_time + self.refresh_time:
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
        self.az_el_dict["Sun"] = self.calculate_az_el("Sun", time, frame)
        self.az_el_dict["Moon"] = self.calculate_az_el("Moon", time, frame)
        self.latest_time = time

    def get_all_azimuth_elevation(self):
        """
        Returns Dictionary Mapping the Objects to their Current AzEl Coordinates
        :return: self.az_el_dict
        """
        return self.az_el_dict

    def get_azimuth_elevation(self, name, time_offset):
        """
        Returns Individual Object AzEl at Specified Time Offset
        :param name: Object Name
        :param time_offset: Any Offset from the Current Time
        :return: (az, el) Tuple
        """
        if time_offset == 0:
            return self.get_all_azimuth_elevation()[name]
        else:
            time = Time.now() + time_offset
            return self.calculate_az_el(
                name, time, AltAz(obstime=time, location=self.location)
            )
