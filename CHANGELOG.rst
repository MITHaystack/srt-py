=================
srt-py Change Log
=================


**Current developments:**

**Added:**

* ``DASHBOARD_THREADS``, ``NPOINT_INTEG_TIME``, ``MINIMAL_ARROWS_DISTANCE``, ``PLAY_SOUNDS``, ``NPOINT_ARROWS``, ``SPECTRUM_HISTORY_LENGTH``, ``WATERFALL_LENGTH``, ``GUI_TIMEZONE``, ``DISPLAY_LIM``, ``DRAW_ECLIPTIC``, ``DRAW_EQUATOR``, ``N_PNT_COUNT``, ``BSWITCH_INTEG_TIME`` parameters
* CASSI motor support
* Baudrate check for H180 and CASSI motors classes
* Non-physical limit warning
* Windrose letters and lines in Azimuth and Elevation Graph
* Buttons to modebar: all shape drawing,  ``togglespikelines`` and ``togglehover``
* Drawing of n-point scan points on az-el graph
* Drawing arrows showing motor route
* ``playsound`` command
* Optional sound when n-point scan and beam switch are complete
* ``rot_curve.txt`` command file
* ``ocl-icd-system`` to the recipe to avoid https://github.com/MITHaystack/srt-py/issues/21#issuecomment-1963827916
* ``tzlocal`` to recipe
* Optional arrows showing route of n-point scan
* ``azel_to_coords.py``, ``coords_to_azel.py``
* Recording indicator to system page
* Waterfall spectrum plot
* Spectrum history length to parameter
* User now can choose timezone in Monitor Page
* Az-el graph display limits to parameter
* Optional drawing of ecliptic and equator planes
* Real size Sun and Moon shapes
* Logging messages to beam switch
* Warning message when angle out of bounds during n-point scan and beam switch
* Log message at the end of n-point scan and beam switch
* Beam switch graph

**Changed:**

* Remember zoom after refresh in Azimuth and Elevation Graph
* Hide Plotly logo
* Enabe scroll zoom
* ``monitor_page.png``
* fk4 to icrs in ``sky_coords.csv``
* Sort the system page by newest issue first
* Different marker types on az el graph
* Marker for visability to circular
* Number of n-point scan rotor positions to parameter
* Height of n-point scan graph to 300
* N-point scan and beam switch integration times to parameters

**Fixed:**

* Searching for default config dir (https://github.com/MITHaystack/srt-py/issues/23)
* Astropy deprecations
* H180 class: init (https://github.com/MITHaystack/srt-py/issues/21) and updating ``self.az_count``, ``self.el_count`` (https://github.com/MITHaystack/srt-py/issues/24)
* N-point scan and beam switch numbering (off-by-one error)
* Conda build error (https://github.com/MITHaystack/srt-py/issues/19)
* N-point scan and beam switch center not updated during scan (https://github.com/MITHaystack/srt-py/issues/25)
* Visability rectangle for negative STOW azimuth (overwritten by: marker for visability to circular)
* Dash deprecation: ``className`` to ``class_name`` (https://github.com/AlexKurek/srt-py/commit/43946aa7e8453154096ddc45c092f506cda00cff)
* ``utcfromtimestamp`` deprecation
* Comment unused modules in ``srt/daemon/radio_control/`` (https://github.com/AlexKurek/srt-py/commit/9a3f9d05a5b0fd2e2b8300441605010e2586599c)
* Graphs appear faster
* Beam switch count (off-by-one error)



v1.1.1
====================

**Added:**

* Dashboard view mode in srt_runner.py
* Visability on dashboard showing beamwdith.



v1.1.0
====================

**Added:**

* Added npoint scan (sinc) interpolation to daemon/utilities/functions.py
* Added npoint scan image to dashboard/layouts/graphs.py
* VLSR calculation added to object_tracker
* VLSR distributed through daemon 
* VLSR shown on display

**Changed:**

* Changed radio_process.grc in the radio directory
* Generated radio_process.py from the grc file and placed in the daemon directory
* Adjusted behavior of npoint scan to have single center point during scan.
* Moved readrad.py to postprocessing folder within main srt folder
* Added baudrate as an option to config/schema file.

**Fixed:**

* Time alignment issues with spectrum and pointing direction.
* Typo in gnuradio grc files and derived python vslr to vlsr.
* Dashboard error from not finding image. MHO images now install with setup and listed in Manifest.in.
* Added shebang to start of scripts.



v1.0.0
====================

**Added:**

* Added npoint scan (sinc) interpolation to daemon/utilities/functions.py
* Added npoint scan image to dashboard/layouts/graphs.py

**Changed:**

* Changed radio_process.grc in the radio directory
* Generated radio_process.py from the grc file and placed in the daemon directory
* Adjusted behavior of npoint scan to have single center point during scan.
* Moved readrad.py to postprocessing folder within main srt folder

**Fixed:**

* Time alignment issues with spectrum and pointing direction.


