# SRT-Py

Small Radio Telescope Control Code for Python

## Description

A Python port of Haystack Observatory's Small Radio Telescope control software.

## Features

 * A New Dash-based Webpage UI for Operating the SRT Remotely
 * GNU Radio Flowgraphs Controlling the Signal Processing of the Antenna
 * Capable of Saving Raw I/Q Samples or Spectrum Data

### Prerequisites

This software is written in pure Python, and so depends on having an installed version of Python 3.6 or newer (although previous versions of Python 3 could be made compatible with only minor tweaks).  For your system, installation instructions for just Python can be found [here](https://www.python.org/downloads/), but it is recommended to instead install [Anaconda](https://docs.anaconda.com/anaconda/install/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) Python in order to take advantage of their dependency management.

## Installation

### Installing from Conda Release Package

# TODO

### Building the Conda Package Locally

 After downloading the srt-py source repository, open up a command prompt or terminal with conda installed and navigate to the folder containing the srt-py directory.  Additionally, ensure that you have conda-build and conda-verify installed

 ```
 conda install conda-build conda-verify
 ```

 Build and install the conda package

 ```
 conda-build srt-py
 conda install -c file://${CONDA_PREFIX}/conda-bld/ srt-py
 ```

### Building the Pip Package Locally (Not Recommended due to Dependency Issues)

After downloading the srt-py source repository, open up a command prompt or terminal with conda installed and navigate to the srt-py directory.  Additionally, it will be necessary to manually install some dependencies, which are specified below, that are not available through PyPI.  If these are not installed, then the following steps will throw an error with the missing dependencies.

Build and install the pip package

 ```
 pip install .
 ```

## Getting Started

  Before using the software, you must create a "config" directory, which should follow the convention set by the example config directory in this repository.  Be sure to change the settings to best match your hardware, celestial objects of interest, and use case.  Please refer to the docs for more information.

  Once installed, you can start the SRT Daemon and SRT Dashboard by running, respectively by executing (for the default runtime options):

  ```
  run_srt_daemon.py --config_dir=PATH_TO_CONFIG_DIR
  run_srt_dashboard.py
  ```

## Example Usage

### Operating via the Dashboard


### Running Headless / Command Line Usage


## Required Libraries

- python >=3.6
- numpy
- scipy
- rtl-sdr
- soapysdr
- soapysdr-module-rtlsdr
- gnuradio-core
- gnuradio-zeromq
- gnuradio-osmosdr
- digital_rf
- pyzmq
- pyserial
- astropy
- yamale
- dash
- dash-bootstrap-components
- plotly
- pandas

## Accommodating Different Hardware


## Further Documentation

More documentation into the specific features of the Small Radio Telescope software are included in the docs directory.

## Other Information


## License


## Acknowledgments
