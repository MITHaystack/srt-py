#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: radio_save_raw
# GNU Radio version: 3.8.1.0

from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
import numpy as np; import gr_digital_rf


class radio_save_raw(gr.top_block):

    def __init__(self, directory_name="./rf_data", samp_rate=2400000):
        gr.top_block.__init__(self, "radio_save_raw")

        ##################################################
        # Parameters
        ##################################################
        self.directory_name = directory_name
        self.samp_rate = samp_rate

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:5558', 100, True, -1)
        self.gr_digital_rf_digital_rf_channel_sink_0 = gr_digital_rf.digital_rf_channel_sink(
            channel_dir=directory_name,
            dtype=np.complex64,
            subdir_cadence_secs=3600,
            file_cadence_millisecs=1000,
            sample_rate_numerator=int(samp_rate),
            sample_rate_denominator=1,
            start='now',
            ignore_tags=False,
            is_complex=True,
            num_subchannels=1,
            uuid_str=None,
            center_frequencies=[],
            metadata={},
            is_continuous=True,
            compression_level=0,
            checksum=False,
            marching_periods=True,
            stop_on_skipped=False,
            stop_on_time_tag=False,
            debug=False,
            min_chunksize=None,
        )



        ##################################################
        # Connections
        ##################################################
        self.connect((self.zeromq_sub_source_0, 0), (self.gr_digital_rf_digital_rf_channel_sink_0, 0))


    def get_directory_name(self):
        return self.directory_name

    def set_directory_name(self, directory_name):
        self.directory_name = directory_name

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate




def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--directory-name", dest="directory_name", type=str, default="./rf_data",
        help="Set ./rf_data [default=%(default)r]")
    parser.add_argument(
        "--samp-rate", dest="samp_rate", type=intx, default=2400000,
        help="Set samp_rate [default=%(default)r]")
    return parser


def main(top_block_cls=radio_save_raw, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(directory_name=options.directory_name, samp_rate=options.samp_rate)

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
