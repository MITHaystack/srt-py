import multiprocessing
from pathlib import Path
from os.path import expanduser
import time

from radio_utils import radio_save_raw

radio_save_raw_process = None


def start_save_raw(samp_rate, root_save_directory):
    print(type(samp_rate))
    global radio_save_raw_process
    if radio_save_raw_process is None:
        directory = time.strftime('SRT_RAW_SAVE-%Y:%m:%d:%H:%M:%S')
        path = str(Path(expanduser(root_save_directory), directory).absolute())
        radio_save_raw_process = multiprocessing.Process(
            target=radio_save_raw.main,
            kwargs={"options": {"directory_name": path, "samp_rate": samp_rate}},
            daemon=True
        )
        radio_save_raw_process.start()
        return True
    else:
        return False


def stop_save_raw():
    global radio_save_raw_process
    if radio_save_raw_process is not None:
        radio_save_raw_process.terminate()
        radio_save_raw_process = None
        return True
    else:
        return False
