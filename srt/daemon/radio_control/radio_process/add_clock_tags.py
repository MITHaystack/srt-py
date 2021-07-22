"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import time
import pmt


def make_time_pair(t):
    return pmt.make_tuple(
        pmt.to_pmt(int(np.trunc(t))), pmt.to_pmt(t - int(np.trunc(t)))
    )


class clk(gr.sync_block):
    def __init__(self, nsamps=8192):
        gr.sync_block.__init__(
            self, name="Add Clock Tags", in_sig=[np.complex64], out_sig=[np.complex64]
        )
        self.pmt_key = pmt.intern("rx_time")
        self.offset = 0
        self.nsamps = nsamps

    def work(self, input_items, output_items):
        nitems = len(input_items[0]) + self.nitems_written(0)
        if self.nitems_written(0) == 0:
            self.add_item_tag(0, 0, self.pmt_key, make_time_pair(time.time()))
        while (nitems - self.offset) > self.nsamps:
            self.offset += self.nsamps
            self.add_item_tag(0, self.offset, self.pmt_key, make_time_pair(time.time()))
        output_items[0][:] = input_items[0]  # copy input to output
        return len(output_items[0])
