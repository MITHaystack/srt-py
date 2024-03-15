## Small Radio Telescope Docs
#### Config Directory Details

The configuration folder for the SRT contains all of the important settings that allow the SRT to operate in different modes and with different default values.  This is split across several different files, including:

 * 'config.yaml' - The main configuration file for the SRT, containing all of the key settings
 * 'sky_coords.csv' - A CSV file listing all celestial objects that the user would like to be able to track automatically

As well as the below, which the user should not typically have to modify:

 * 'schema.yaml' - The schema for config.yaml, which lists the valid range of options in config.yaml
 * 'calibration.json' - A JSON containing the calibration data from the most recent time the calibrate command was running

If the user wants to add configuration options within these files they must update schema.yaml and config.yaml and make sure they are in the same directory together when calling srt_runner.py.
##### config.yaml

The config.yaml file contains the following settings:

* STATION - The latitude, longitude, and name of the location of the SRT.
```YAML
STATION:
  latitude: 42.5
  longitude: -71.5
  name: Haystack
```

* EMERGENCY_CONTACT - The emergency contact info that will show up on the SRT Dashboard in case anything happens with the SRT
```YAML
EMERGENCY_CONTACT:
  name: John Doe
  email: test@example.com
  phone_number: 555-555-5555
```

* AZLIMITS - The range of movement of the SRT's motor controller along the azimuth, given clockwise in degrees
```YAML
AZLIMITS:
  lower_bound: 38.0
  upper_bound: 355.0
```

* ELLIMITS - The range of movement of the SRT's motor controller in elevation, given in degrees
```YAML
ELLIMITS:
  lower_bound: 0.0
  upper_bound: 89.0
```

* STOW_LOCATION - The azimuth and elevation that the 'stow' command should return the SRT to
```YAML
STOW_LOCATION:
  azimuth: 38.0
  elevation: 0.0
```

* CAL_LOCATION - The azimuth and elevation for calibration of the SRT to be performed against.  For example, for the SRT at Haystack Observatory, this points to a thick cluster of trees so that the sky cannot be seen and noise can be evaluated comparatively.
```YAML
CAL_LOCATION:
  azimuth: 120.0
  elevation: 7.0
```

* MOTOR_TYPE - The type of motor being used.  Several different types are currently allowed, include NONE (which works for either a fixed antenna or simulating on a system without an antenna), ALFASPID (which works with any ROT2 protocol supporting motor), H180MOUNT (which works with the H180 motor on some SRTs), CASSI (which works with the CASSI Corp. mount) and PUSHROD (which works with the old custom pushrod system of the SRT).  Currently, since the SRT at Haystack uses a ALFASPID motor, that is the only one which has currently been extensively tested.  Additionally, please refer to the in-code documentation in srt/daemon/rotor_control for more information on adding support for more motors.
```YAML
MOTOR_TYPE: NONE
```

* MOTOR_PORT - The location of the motor on the host system.  For example, on a Unix system this will probably be some device like '/dev/ttyUSB0', on Mac is will be something like '/dev/tty.usbserial-A602P777' and on Windows this will be a COM port like 'COM3'.  This is not used if MOTOR_TYPE is NONE.
```YAML
MOTOR_PORT: /dev/ttyUSB0
```

* MOTOR_BAUDRATE - The baudrate for the serial connection to the motor controller. The ALFASPID motor baudrate can vary depending on the specific model, the ROT2PROG is 600, while the MD-01/MD-02 default setting is 460800. This can be changed and see the instruction manual to learn how to set and check this value. The H180MOUNT is 2400 and the PUSHROD is 2000. This is not used if MOTOR_TYPE is NONE.
```YAML
MOTOR_BAUDRATE: 600
```

* RADIO_CF - The default center frequency of the SRT in Hz.  The center frequency of the SRT can be changed during run-time, but this is the default and initial value on startup.
```YAML
RADIO_CF: 1420000000
```

* RADIO_SF - The sample frequency of the SRT in Hz.  Since SDRs typically take both an I and Q sample at this rate, the sample frequency is conveniently also the effective bandwidth.  This can be changed during run-time, but this is the default and initial value on startup.
```YAML
RADIO_SF: 2000000
```

* RADIO_NUM_BINS - The number of bins that the FFT will output.  More bins means a more precise spectrum, but at a higher computational cost.
```YAML
RADIO_NUM_BINS: 4096
```

* RADIO_INTEG_CYCLES - The number of FFT output arrays to average over before saving or displaying the result.  Higher values means a more accurate spectrum, but less frequently updating.  Note that the integration time can be calculated using RADIO_NUM_BINS * RADIO_INTEG_CYCLES / RADIO_SF.
```YAML
RADIO_INTEG_CYCLES: 1000
```

* RADIO_AUTOSTART - Whether to automatically start the GNU Radio script that performs the FFT and integration when the program starts.  Keep this True for default behavior, but if a custom radio processing script is desired, make this false and run your own following the input and outputs used in radio/radio_processing to make sure all the data gets to the right places
```YAML
RADIO_AUTOSTART: Yes
```

* BEAMWIDTH - The half-power beamwidth of the antenna being used, in degrees
```YAML
BEAMWIDTH: 7.0
```

* TSYS - The estimated system temperature of the radio dish and its path to the receiver, in Kelvin
```YAML
TSYS: 171
```

* TCAL - The temperature of the calibration source (~300K for a typical object on earth), in Kelvin
```YAML
TCAL: 290
```

* SAVE_DIRECTORY - The folder to save any recordings the SRT will produce
```YAML
SAVE_DIRECTORY: ~/Desktop/SRT-Saves
```

* DASHBOARD_REFRESH_MS - The number of milliseconds for dashboard refresh.
```YAML
DASHBOARD_REFRESH_MS: 3000
```

* DASHBOARD_THREADS - The number of threads for dash. 8 seems to be enought at the host. If also a client is connected and you are getting `WARNING:waitress.queue:Task queue depth is 1`, consider increasing this value.
```YAML
DASHBOARD_THREADS: 8
```
##### sky_coords.csv

The sky_coords data file is organized into four columns, with a row for each entry.
* The first column is the coordinate system of the celestial object, which supports any coordinate system name recognized by AstroPy, and has been tested with 'fk4' and 'galactic'.
* The next two columns are the first and second coordinate of the object, such as ra and dec for fk4 and l and b for galactic.
* The last column is the name of the object.

All points listed here will show up as points on the Dashboard, and the SRT will be able to track their movements.  Additionally, their names will become keywords in command files, so to point at a object given the name Orion, the command would just be 'Orion'.

Below is an example excerpt of a sky_coords.csv file:
```CSV
coordinate_system,coordinate_a,coordinate_b,name
fk4,05 31 30,21 58 00,Crab
fk4,05 32 48,-5 27 00,Orion
fk4,05 42 00,-1 00 00,S8
galactic,10,1,RC_CLOUD
galactic,00,0,G00
```
