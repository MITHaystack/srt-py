import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time


object_str = 'Orion Nebula'
object = SkyCoord.from_name(object_str)

location = EarthLocation(lat=50.0465664*u.deg, lon=19.8279168*u.deg, height=313*u.m)
utcoffset = +2*u.hour
time = Time('2024-4-19 12:41:00') - utcoffset

altaz = object.transform_to(AltAz(obstime=time, location=location))

print("Object: ", object_str)
print(f"Altitude   = {altaz.alt}")
print(f"Longtitude = {altaz.az}")
