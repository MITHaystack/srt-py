import multiprocessing
from pathlib import Path
from os.path import expanduser
from argparse import Namespace
import time

from radio_control import radio_process
from radio_control import radio_save_raw
from radio_control import radio_calibrate


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
    def __init__(self, samp_rate, root_save_directory):
        directory = time.strftime("SRT_RAW_SAVE-%Y:%m:%d:%H:%M:%S")
        path = str(Path(expanduser(root_save_directory), directory).absolute())
        super().__init__(radio_save_raw.main, directory_name=path, samp_rate=samp_rate)


class RadioCalibrateTask(RadioTask):
    def __init__(self, num_bins, num_integrations, config_directory):
        path = str(Path(expanduser(config_directory)).absolute())
        super().__init__(
            radio_calibrate.main,
            directory_name=path,
            num_bins=num_bins,
            num_integrations=num_integrations,
        )
