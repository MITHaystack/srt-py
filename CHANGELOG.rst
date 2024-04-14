=================
srt-py Change Log
=================

.. current developments

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


