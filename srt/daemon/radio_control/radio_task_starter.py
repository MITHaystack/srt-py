import multiprocessing
from pathlib import Path
from os.path import expanduser
from argparse import Namespace
import time

from .radio_process import radio_process
from .radio_calibrate import radio_calibrate
from .radio_save_raw import radio_save_raw
from .radio_save_spec_rad import radio_save_spec
from .radio_save_spec_fits import radio_save_spec_fits


class RadioTask(multiprocessing.Process):
    """
    Multiprocessing Wrapper Process Superclass for Calling Unmodified GNU Radio Companion Scripts
    """
    def __init__(self, main_method, **kwargs):
        super().__init__(
            target=main_method, kwargs={"options": Namespace(**kwargs)}, daemon=True,
        )


class RadioProcessTask(RadioTask):
    """
    Multiprocessing Wrapper Process for Starting the Processing of Radio Signals
    """
    def __init__(self, num_bins, num_integrations):
        super().__init__(
            radio_process.main, num_bins=num_bins, num_integrations=num_integrations
        )


class RadioSaveRawTask(RadioTask):
    """
    Multiprocessing Wrapper Process for Saving Raw I/Q Samples
    """
    def __init__(self, samp_rate, root_save_directory, directory):
        if directory is None:
            directory = time.strftime("SRT_RAW_SAVE-%Y:%m:%d:%H:%M:%S")
        path = str(Path(expanduser(root_save_directory), directory).absolute())
        super().__init__(radio_save_raw.main, directory_name=path, samp_rate=samp_rate)


class RadioSaveSpecRadTask(RadioTask):
    """
    Multiprocessing Wrapper Process for Saving Spectrum Data in .rad Files
    """
    def __init__(self, samp_rate, num_bins, root_save_directory, file_name):
        if file_name is None:
            file_name = time.strftime("%y:%j:%H.rad")
        path = str(Path(expanduser(root_save_directory)).absolute())
        super().__init__(
            radio_save_spec.main,
            directory_name=path,
            samp_rate=samp_rate,
            num_bins=num_bins,
            file_name=file_name,
        )


class RadioSaveSpecFitsTask(RadioTask):
    """
    Multiprocessing Wrapper Process for Saving Spectrum Data in .fits Files
    """
    def __init__(self, samp_rate, num_bins, root_save_directory, file_name):
        if file_name is None:
            file_name = time.strftime("SRT_SPEC_SAVE-%Y:%m:%d:%H:%M:%S.fits")
        path = str(Path(expanduser(root_save_directory)).absolute())
        super().__init__(
            radio_save_spec_fits.main,
            directory_name=path,
            samp_rate=samp_rate,
            num_bins=num_bins,
            file_name=file_name,
        )


class RadioCalibrateTask(RadioTask):
    """
    Multiprocessing Wrapper Process for Generating a New calibration.json
    """
    def __init__(self, num_bins, config_directory):
        path = str(Path(expanduser(config_directory)).absolute())
        super().__init__(
            radio_calibrate.main,
            directory_name=path,
            num_bins=num_bins,
        )
