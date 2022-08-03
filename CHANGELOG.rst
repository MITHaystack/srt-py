=================
srt-py Change Log
=================

.. current developments

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


