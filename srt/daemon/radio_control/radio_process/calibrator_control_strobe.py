"""
block to generate calibrator control commands for the X300 radio. 
note that this block assumes a latency lower than the calibrator cycle time
and will break if that condition is not met

Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""
import numpy as np
from gnuradio import gr 
import pmt
import time
import uhd

class msg_blk(gr.sync_block):
    def __init__(self, calibrator_mask=0xFFF,cal_state=False):
        gr.sync_block.__init__(
            self,
            name="calibrator_msg_block",
            in_sig=None,
           out_sig=None
        )

        #input parameters
        self.calibrator_mask = calibrator_mask
        self.cal_state = cal_state

        #derived variables

        self.last_cal_state = False
        #self.cal_value = 0x000
        
        self.message_port_register_in(pmt.intern('strobe'))
        self.message_port_register_out(pmt.intern('command'))
        
        self.set_msg_handler(pmt.intern('strobe'), self.handle_msg)

    def handle_msg(self, msg):

        #send message to define next calibrator state change

        if self.last_cal_state != self.cal_state:
            if self.cal_state:
                cal_value = 0xFFF
            else:
                cal_value = 0x000
                
            #issue command to toggle gpio
            set_gpio = pmt.make_dict()
            set_gpio = pmt.dict_add(set_gpio, pmt.to_pmt('bank'), pmt.to_pmt('FP0A'))
            set_gpio = pmt.dict_add(set_gpio, pmt.to_pmt('attr'), pmt.to_pmt('OUT'))
            set_gpio = pmt.dict_add(set_gpio, pmt.to_pmt('value'), pmt.from_double(cal_value))
            set_gpio = pmt.dict_add(set_gpio, pmt.to_pmt('mask'), pmt.from_double(self.calibrator_mask))
            
            msg = pmt.make_dict()
            msg = pmt.dict_add(msg, pmt.to_pmt('gpio'), set_gpio)
            self.message_port_pub(pmt.intern('command'), msg) #issue message
            
            self.last_cal_state = self.cal_state
            
        #otherwise do nothing        
