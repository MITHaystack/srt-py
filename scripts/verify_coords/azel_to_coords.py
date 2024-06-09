#!/usr/bin/env python
"""azel_to_coords.py

Calculates Coords from Az, El. Helps to create test objects for sky_coords.csv.

"""
import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
from pytz import timezone

if __name__ == "__main__":
    location = EarthLocation(
        lat=50.0465664 * u.deg, lon=19.8279168 * u.deg, height=313 * u.m
    )

    # custom time
    # utcoffset = +2*u.hour
    # time = Time('2024-4-19 12:41:00') - utcoffset

    # current time
    tz = timezone("Europe/Warsaw")
    time = Time.now()
    time = time.to_datetime(timezone=tz)

    coords = SkyCoord(
        20, 20, frame="altaz", unit="deg", obstime=time, location=location
    )
    icrs = coords.transform_to("icrs")

    az = icrs.ra
    el = icrs.dec

    ra = az.to_string(unit=u.hour, sep=" ", precision=0)
    dec = el.to_string(unit=u.deg, sep=" ", precision=0)

    print(f"Coords = {coords}")
    print(f"ra  = {ra}")
    print(f"dec = {dec}")
