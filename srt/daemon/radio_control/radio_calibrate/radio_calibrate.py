#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: radio_calibrate
# GNU Radio version: 3.8.1.0

from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
from . import save_calibration


class radio_calibrate(gr.top_block):

    def __init__(self, directory_name=".", num_bins=4096):
        gr.top_block.__init__(self, "radio_calibrate")

        ##################################################
        # Parameters
        ##################################################
        self.directory_name = directory_name
        self.num_bins = num_bins

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_float, num_bins, 'tcp://127.0.0.1:5560', 100, True, -1)
        self.save_calibration = save_calibration.blk(directory=directory_name, filename='calibration.json', vec_length=num_bins, poly_smoothing_order=25)



        ##################################################
        # Connections
        ##################################################
        self.connect((self.zeromq_sub_source_0, 0), (self.save_calibration, 0))


    def get_directory_name(self):
        return self.directory_name

    def set_directory_name(self, directory_name):
        self.directory_name = directory_name
        self.save_calibration.directory = self.directory_name

    def get_num_bins(self):
        return self.num_bins

    def set_num_bins(self, num_bins):
        self.num_bins = num_bins
        self.save_calibration.vec_length = self.num_bins




def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--directory-name", dest="directory_name", type=str, default=".",
        help="Set . [default=%(default)r]")
    parser.add_argument(
        "--num-bins", dest="num_bins", type=intx, default=4096,
        help="Set num_bins [default=%(default)r]")
    return parser


def main(top_block_cls=radio_calibrate, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(directory_name=options.directory_name, num_bins=options.num_bins)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()


if __name__ == '__main__':
    main()
