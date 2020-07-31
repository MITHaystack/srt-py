"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
import numpy.polynomial.polynomial as poly
import json

from gnuradio import gr
import pmt

import pathlib


class blk(gr.sync_block):
    """Embedded Python Block - Calculate Calibration Values"""

    def __init__(
        self,
        directory=".",
        filename="calibration.json",
        vec_length=4096,
        poly_smoothing_order=25,
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
        self.poly_smoothing_order = poly_smoothing_order
        self.past_input = np.zeros(vec_length)
        self.num_past_input = 0

    def work(self, input_items, output_items):
        """Divide Input by Average, Determine Calibration Power, and Save"""
        for input_array in input_items[0]:
            self.past_input += input_array
            self.num_past_input += 1
            averaged_input = self.past_input / self.num_past_input
            relative_freq_values = np.linspace(-1, 1, self.vec_length)
            poly_fit = poly.Polynomial.fit(
                relative_freq_values, averaged_input, self.poly_smoothing_order,
            )
            smoothed_input = poly_fit(relative_freq_values)
            average_value = np.average(smoothed_input)
            rescaled_input = smoothed_input / average_value
            file_output = {
                "cal_pwr": average_value,
                "cal_values": rescaled_input.tolist(),
            }
            with open(pathlib.Path(self.directory, self.filename), "w") as outfile:
                json.dump(file_output, outfile)
        return len(input_items[0])
