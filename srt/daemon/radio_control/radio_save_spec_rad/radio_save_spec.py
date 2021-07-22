#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: radio_save_spec
# GNU Radio version: 3.8.1.0

from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
from . import save_rad_file


class radio_save_spec(gr.top_block):
    def __init__(
        self, directory_name=".", file_name="test.rad", num_bins=4096, samp_rate=2400000
    ):
        gr.top_block.__init__(self, "radio_save_spec")

        ##################################################
        # Parameters
        ##################################################
        self.directory_name = directory_name
        self.file_name = file_name
        self.num_bins = num_bins
        self.samp_rate = samp_rate

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_sub_source_0 = zeromq.sub_source(
            gr.sizeof_float, num_bins, "tcp://127.0.0.1:5562", 100, True, -1
        )
        self.save_rad_file = save_rad_file.blk(
            directory=directory_name, filename=file_name, vec_length=num_bins
        )

        ##################################################
        # Connections
        ##################################################
        self.connect((self.zeromq_sub_source_0, 0), (self.save_rad_file, 0))

    def get_directory_name(self):
        return self.directory_name

    def set_directory_name(self, directory_name):
        self.directory_name = directory_name
        self.save_rad_file.directory = self.directory_name

    def get_file_name(self):
        return self.file_name

    def set_file_name(self, file_name):
        self.file_name = file_name
        self.save_rad_file.filename = self.file_name

    def get_num_bins(self):
        return self.num_bins

    def set_num_bins(self, num_bins):
        self.num_bins = num_bins
        self.save_rad_file.vec_length = self.num_bins

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate


def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--directory-name",
        dest="directory_name",
        type=str,
        default=".",
        help="Set . [default=%(default)r]",
    )
    parser.add_argument(
        "--file-name",
        dest="file_name",
        type=str,
        default="test.rad",
        help="Set test.rad [default=%(default)r]",
    )
    parser.add_argument(
        "--num-bins",
        dest="num_bins",
        type=intx,
        default=4096,
        help="Set num_bins [default=%(default)r]",
    )
    parser.add_argument(
        "--samp-rate",
        dest="samp_rate",
        type=intx,
        default=2400000,
        help="Set samp_rate [default=%(default)r]",
    )
    return parser


def main(top_block_cls=radio_save_spec, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(
        directory_name=options.directory_name,
        file_name=options.file_name,
        num_bins=options.num_bins,
        samp_rate=options.samp_rate,
    )

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()


if __name__ == "__main__":
    main()
