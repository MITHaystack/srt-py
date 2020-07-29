"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
import json

from gnuradio import gr
import pmt

import pathlib


class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block - Calculate Calibration Values"""

    def __init__(self, directory=".", filename="test.rad", vec_length=4096):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Embedded Python Block',   # will show up in GRC
            in_sig=[(np.float32, vec_length)],
            out_sig=None
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.directory = directory
        self.filename = filename
        self.vec_length = vec_length

    def work(self, input_items, output_items):
        """Divide Input by Average, Determine Calibration Power, and Save"""
        averaged_input = np.zeros(len(input_items[0][0]))
        for input_array in input_items[0]:
            averaged_input += input_array
        averaged_input /= len(input_items[0])
        average_value = np.average(averaged_input)
        averaged_input /= average_value
        file_output = {"cal_pwr": average_value, "cal_values": averaged_input.tolist()}
        with open(pathlib.Path(self.directory, self.filename),"w") as outfile:
            json.dump(file_output, outfile)
        return len(input_items[0])
