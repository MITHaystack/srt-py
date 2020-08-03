import multiprocessing
from pathlib import Path
from os.path import expanduser
from argparse import Namespace
import time

from . import radio_process, radio_save_raw, radio_calibrate, radio_save_spec


class RadioTask(multiprocessing.Process):
    def __init__(self, main_method, **kwargs):
        super().__init__(
            target=main_method, kwargs={"options": Namespace(**kwargs)}, daemon=True,
        )


class RadioProcessTask(RadioTask):
    def __init__(self, num_bins, num_integrations):
        super().__init__(
            radio_process.main, num_bins=num_bins, num_integrations=num_integrations
        )


class RadioSaveRawTask(RadioTask):
    def __init__(self, samp_rate, root_save_directory, directory):
        if directory is None:
            directory = time.strftime("SRT_RAW_SAVE-%Y:%m:%d:%H:%M:%S")
        path = str(Path(expanduser(root_save_directory), directory).absolute())
        super().__init__(radio_save_raw.main, directory_name=path, samp_rate=samp_rate)


class RadioSaveSpecRadTask(RadioTask):
    def __init__(self, samp_rate, num_bins, root_save_directory, file_name):
        if file_name is None:
            file_name = time.strftime("%y:%j:%H")
        path = str(Path(expanduser(root_save_directory)).absolute())
        super().__init__(
            radio_save_spec.main,
            directory_name=path,
            samp_rate=samp_rate,
            num_bins=num_bins,
            file_name=file_name,
        )


class RadioCalibrateTask(RadioTask):
    def __init__(self, num_bins, num_integrations, config_directory):
        path = str(Path(expanduser(config_directory)).absolute())
        super().__init__(
            radio_calibrate.main,
            directory_name=path,
            num_bins=num_bins,
            num_integrations=num_integrations,
        )