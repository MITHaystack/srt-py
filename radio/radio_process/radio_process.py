#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: radio_process
# GNU Radio version: 3.8.1.0

from gnuradio import blocks
import pmt
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
import xmlrpc.server
import threading
import epy_block_0_0
import numpy as np
import osmosdr
import time


class radio_process(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "radio_process")

        ##################################################
        # Variables
        ##################################################
        self.fft_size = fft_size = 8192
        self.sinc_sample_locations = sinc_sample_locations = np.arange(-np.pi*4/2.0, np.pi*4/2.0, np.pi/fft_size)
        self.sinc = sinc = np.sinc(sinc_sample_locations/np.pi)
        self.samp_rate = samp_rate = 2400000
        self.num_integrations = num_integrations = 1000
        self.motor_el = motor_el = np.nan
        self.motor_az = motor_az = np.nan
        self.is_running = is_running = False
        self.freq = freq = 1420000000
        self.custom_window = custom_window = sinc*np.hamming(4*fft_size)

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_pub_sink_1_0 = zeromq.pub_sink(gr.sizeof_float, fft_size, 'tcp://127.0.0.1:5560', 100, False, -1)
        self.zeromq_pub_sink_1 = zeromq.pub_sink(gr.sizeof_float, fft_size, 'tcp://127.0.0.1:5561', 100, True, -1)
        self.zeromq_pub_sink_0_0 = zeromq.pub_sink(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:5559', 100, False, -1)
        self.zeromq_pub_sink_0 = zeromq.pub_sink(gr.sizeof_gr_complex, pow(2, 16), 'tcp://127.0.0.1:5558', 100, True, -1)
        self.xmlrpc_server_0 = xmlrpc.server.SimpleXMLRPCServer(('localhost', 5557), allow_none=True)
        self.xmlrpc_server_0.register_instance(self)
        self.xmlrpc_server_0_thread = threading.Thread(target=self.xmlrpc_server_0.serve_forever)
        self.xmlrpc_server_0_thread.daemon = True
        self.xmlrpc_server_0_thread.start()
        self.osmosdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + "soapy=0"
        )
        self.osmosdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(100e6, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_gain(10, 0)
        self.osmosdr_source_0.set_if_gain(20, 0)
        self.osmosdr_source_0.set_bb_gain(20, 0)
        self.osmosdr_source_0.set_antenna('', 0)
        self.osmosdr_source_0.set_bandwidth(0, 0)
        self.fft_vxx_0 = fft.fft_vcc(fft_size, True, window.blackmanharris(fft_size), True, 1)
        self.epy_block_0_0 = epy_block_0_0.clk(nsamps=fft_size*4)
        self.dc_blocker_xx_0 = filter.dc_blocker_cc(fft_size, True)
        self.blocks_tags_strobe_0_0 = blocks.tags_strobe(gr.sizeof_gr_complex*1, pmt.to_pmt({"fft_size": fft_size, "samp_rate": samp_rate, "num_integrations": num_integrations, "motor_az": motor_az, "motor_el": motor_el, "freq": freq}), fft_size*4, pmt.intern("metadata"))
        self.blocks_tags_strobe_0 = blocks.tags_strobe(gr.sizeof_gr_complex*1, pmt.to_pmt(float(freq)), fft_size*4, pmt.intern("rx_freq"))
        self.blocks_stream_to_vector_0_2_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, pow(2, 16))
        self.blocks_stream_to_vector_0_2 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_size)
        self.blocks_stream_to_vector_0_1 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_size)
        self.blocks_stream_to_vector_0_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_size)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_size)
        self.blocks_selector_0 = blocks.selector(gr.sizeof_gr_complex*1,0,0)
        self.blocks_selector_0.set_enabled(True)
        self.blocks_nlog10_ff_0 = blocks.nlog10_ff(10, fft_size, 0)
        self.blocks_multiply_const_vxx_0_0_0_0 = blocks.multiply_const_vcc(custom_window[0:fft_size])
        self.blocks_multiply_const_vxx_0_0_0 = blocks.multiply_const_vcc(custom_window[fft_size:2*fft_size])
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_vcc(custom_window[2*fft_size:3*fft_size])
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc(custom_window[-fft_size:])
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(num_integrations, 1, 4000, fft_size)
        self.blocks_message_strobe_0 = blocks.message_strobe(pmt.to_pmt(is_running), 100)
        self.blocks_integrate_xx_0 = blocks.integrate_ff(num_integrations, fft_size)
        self.blocks_delay_0_1 = blocks.delay(gr.sizeof_gr_complex*1, fft_size)
        self.blocks_delay_0_0 = blocks.delay(gr.sizeof_gr_complex*1, fft_size*2)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_gr_complex*1, fft_size*3)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(fft_size)
        self.blocks_add_xx_0_0 = blocks.add_vcc(1)
        self.blocks_add_xx_0 = blocks.add_vcc(fft_size)



        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self.blocks_selector_0, 'en'))
        self.connect((self.blocks_add_xx_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.blocks_add_xx_0_0, 0), (self.blocks_selector_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_integrate_xx_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.blocks_stream_to_vector_0_2, 0))
        self.connect((self.blocks_delay_0_0, 0), (self.blocks_stream_to_vector_0_0, 0))
        self.connect((self.blocks_delay_0_1, 0), (self.blocks_stream_to_vector_0_1, 0))
        self.connect((self.blocks_integrate_xx_0, 0), (self.zeromq_pub_sink_1, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_nlog10_ff_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_multiply_const_vxx_0_0_0, 0), (self.blocks_add_xx_0, 2))
        self.connect((self.blocks_multiply_const_vxx_0_0_0_0, 0), (self.blocks_add_xx_0, 3))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.zeromq_pub_sink_1_0, 0))
        self.connect((self.blocks_selector_0, 0), (self.blocks_stream_to_vector_0_2_0, 0))
        self.connect((self.blocks_selector_0, 0), (self.dc_blocker_xx_0, 0))
        self.connect((self.blocks_selector_0, 0), (self.zeromq_pub_sink_0_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_stream_to_vector_0_0, 0), (self.blocks_multiply_const_vxx_0_0_0, 0))
        self.connect((self.blocks_stream_to_vector_0_1, 0), (self.blocks_multiply_const_vxx_0_0, 0))
        self.connect((self.blocks_stream_to_vector_0_2, 0), (self.blocks_multiply_const_vxx_0_0_0_0, 0))
        self.connect((self.blocks_stream_to_vector_0_2_0, 0), (self.zeromq_pub_sink_0, 0))
        self.connect((self.blocks_tags_strobe_0, 0), (self.blocks_add_xx_0_0, 0))
        self.connect((self.blocks_tags_strobe_0_0, 0), (self.blocks_add_xx_0_0, 2))
        self.connect((self.dc_blocker_xx_0, 0), (self.blocks_delay_0, 0))
        self.connect((self.dc_blocker_xx_0, 0), (self.blocks_delay_0_0, 0))
        self.connect((self.dc_blocker_xx_0, 0), (self.blocks_delay_0_1, 0))
        self.connect((self.dc_blocker_xx_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.epy_block_0_0, 0), (self.blocks_add_xx_0_0, 1))
        self.connect((self.fft_vxx_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.epy_block_0_0, 0))


    def get_fft_size(self):
        return self.fft_size

    def set_fft_size(self, fft_size):
        self.fft_size = fft_size
        self.set_custom_window(self.sinc*np.hamming(4*self.fft_size))
        self.set_sinc_sample_locations(np.arange(-np.pi*4/2.0, np.pi*4/2.0, np.pi/self.fft_size))
        self.blocks_delay_0.set_dly(self.fft_size*3)
        self.blocks_delay_0_0.set_dly(self.fft_size*2)
        self.blocks_delay_0_1.set_dly(self.fft_size)
        self.blocks_multiply_const_vxx_0.set_k(self.custom_window[-self.fft_size:])
        self.blocks_multiply_const_vxx_0_0.set_k(self.custom_window[2*self.fft_size:3*self.fft_size])
        self.blocks_multiply_const_vxx_0_0_0.set_k(self.custom_window[self.fft_size:2*self.fft_size])
        self.blocks_multiply_const_vxx_0_0_0_0.set_k(self.custom_window[0:self.fft_size])
        self.blocks_tags_strobe_0.set_nsamps(self.fft_size*4)
        self.blocks_tags_strobe_0_0.set_value(pmt.to_pmt({"fft_size": self.fft_size, "samp_rate": self.samp_rate, "num_integrations": self.num_integrations, "motor_az": self.motor_az, "motor_el": self.motor_el, "freq": self.freq}))
        self.blocks_tags_strobe_0_0.set_nsamps(self.fft_size*4)

    def get_sinc_sample_locations(self):
        return self.sinc_sample_locations

    def set_sinc_sample_locations(self, sinc_sample_locations):
        self.sinc_sample_locations = sinc_sample_locations
        self.set_sinc(np.sinc(self.sinc_sample_locations/np.pi))

    def get_sinc(self):
        return self.sinc

    def set_sinc(self, sinc):
        self.sinc = sinc
        self.set_custom_window(self.sinc*np.hamming(4*self.fft_size))
        self.set_sinc(np.sinc(self.sinc_sample_locations/np.pi))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_tags_strobe_0_0.set_value(pmt.to_pmt({"fft_size": self.fft_size, "samp_rate": self.samp_rate, "num_integrations": self.num_integrations, "motor_az": self.motor_az, "motor_el": self.motor_el, "freq": self.freq}))
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)

    def get_num_integrations(self):
        return self.num_integrations

    def set_num_integrations(self, num_integrations):
        self.num_integrations = num_integrations
        self.blocks_moving_average_xx_0.set_length_and_scale(self.num_integrations, 1)
        self.blocks_tags_strobe_0_0.set_value(pmt.to_pmt({"fft_size": self.fft_size, "samp_rate": self.samp_rate, "num_integrations": self.num_integrations, "motor_az": self.motor_az, "motor_el": self.motor_el, "freq": self.freq}))

    def get_motor_el(self):
        return self.motor_el

    def set_motor_el(self, motor_el):
        self.motor_el = motor_el
        self.blocks_tags_strobe_0_0.set_value(pmt.to_pmt({"fft_size": self.fft_size, "samp_rate": self.samp_rate, "num_integrations": self.num_integrations, "motor_az": self.motor_az, "motor_el": self.motor_el, "freq": self.freq}))

    def get_motor_az(self):
        return self.motor_az

    def set_motor_az(self, motor_az):
        self.motor_az = motor_az
        self.blocks_tags_strobe_0_0.set_value(pmt.to_pmt({"fft_size": self.fft_size, "samp_rate": self.samp_rate, "num_integrations": self.num_integrations, "motor_az": self.motor_az, "motor_el": self.motor_el, "freq": self.freq}))

    def get_is_running(self):
        return self.is_running

    def set_is_running(self, is_running):
        self.is_running = is_running
        self.blocks_message_strobe_0.set_msg(pmt.to_pmt(self.is_running))

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.blocks_tags_strobe_0.set_value(pmt.to_pmt(float(self.freq)))
        self.blocks_tags_strobe_0_0.set_value(pmt.to_pmt({"fft_size": self.fft_size, "samp_rate": self.samp_rate, "num_integrations": self.num_integrations, "motor_az": self.motor_az, "motor_el": self.motor_el, "freq": self.freq}))

    def get_custom_window(self):
        return self.custom_window

    def set_custom_window(self, custom_window):
        self.custom_window = custom_window
        self.blocks_multiply_const_vxx_0.set_k(self.custom_window[-self.fft_size:])
        self.blocks_multiply_const_vxx_0_0.set_k(self.custom_window[2*self.fft_size:3*self.fft_size])
        self.blocks_multiply_const_vxx_0_0_0.set_k(self.custom_window[self.fft_size:2*self.fft_size])
        self.blocks_multiply_const_vxx_0_0_0_0.set_k(self.custom_window[0:self.fft_size])





def main(top_block_cls=radio_process, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
