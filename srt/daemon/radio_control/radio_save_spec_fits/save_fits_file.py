"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt
import json

import pathlib
from datetime import datetime, timezone
from astropy.io import fits


class blk(gr.sync_block):
    """Embedded Python Block - Saving"""

    def __init__(
        self, directory=".", filename="test.fits", vec_length=4096
    ):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name="Embedded Python Block",  # will show up in GRC
            in_sig=[(np.float32, vec_length)],
            out_sig=None,
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.directory = directory
        self.filename = filename
        self.vec_length = vec_length

    def work(self, input_items, output_items):
        """Saving Spectrum Data to a FITS File"""
        file_path = pathlib.Path(self.directory, self.filename)
        for i, input_array in enumerate(input_items[0]):
            file = open(file_path, "ab+")
            tags = self.get_tags_in_window(0, 0, len(input_items[0]))
            tags_dict = {
                pmt.to_python(tag.key): pmt.to_python(tag.value) for tag in tags
            }
            time_since_epoch = tags_dict["rx_time"][0] + tags_dict["rx_time"][1]
            date = datetime.fromtimestamp(time_since_epoch, timezone.utc)
            metadata = tags_dict["metadata"]
            samp_rate = metadata["samp_rate"]
            num_integrations = metadata["num_integrations"]
            freq = metadata["freq"]
            num_bins = metadata["num_bins"]
            soutrack = metadata["soutrack"]

            hdr = fits.Header()
            hdr["BUNIT"] = "K"
            hdr["CTYPE1"] = "Freq"
            hdr["CRPIX1"] = num_bins / float(2)  # Reference pixel (center)
            hdr["CRVAL1"] = freq  # Center, USRP, frequency
            hdr["CDELT1"] = samp_rate / (1 * num_bins)  # Channel width
            hdr["CUNIT1"] = "Hz"

            hdr["TELESCOP"] = "SmallRadioTelescope"
            hdr["OBJECT"] = soutrack
            hdr["OBSTIME"] = (num_bins * num_integrations) / samp_rate

            hdr["DATE-OBS"] = date.strftime("%Y-%m-%d")
            hdr["UTC"] = date.strftime("%H:%M:00%s")
            hdr["METADATA"] = json.dumps(metadata)

            fits.append(file, input_array, hdr)
            file.close()
            # p = np.sum(input_array)
            # a = len(input_array)
            # pwr = (tsys + tcal) * p / (a * calpwr)
            # ppwr = pwr - tsys
        return len(input_items[0])
