"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt

import pathlib
from datetime import datetime, timezone
from math import sqrt


# String Formatting Constants
header_format = (
    "DATE %4d:%03d:%02d:%02d:%02d obsn %3d az %4.1f el %3.1f freq_MHz "
    "%10.4f Tsys %6.3f Tant %6.3f vlsr %7.2f glat %6.3f glon %6.3f source %s\n"
)
start_format = (
    "Fstart %8.3f fstop %8.3f spacing %8.6f bw %8.3f fbw %8.3f MHz nfreq "
    "%d nsam %d npoint %d integ %5.0f sigma %8.3f bsw %d\n"
)
integration_format = "Spectrum %6.0f integration periods\n"
number_format = "%8.3f "


def parse_time(rx_time):
    time_since_epoch = rx_time[0] + rx_time[1]
    date = datetime.fromtimestamp(time_since_epoch, timezone.utc)
    new_year_day = datetime(year=date.year, month=1, day=1, tzinfo=timezone.utc)
    day_of_year = (date - new_year_day).days + 1
    return date.year, day_of_year, date.hour, date.minute, date.second


def parse_metadata(metadata):
    motor_az = metadata["motor_az"]
    motor_el = metadata["motor_el"]
    samp_rate = metadata["samp_rate"]
    num_integrations = metadata["num_integrations"]
    freq = metadata["freq"]
    num_bins = metadata["num_bins"]
    tsys = metadata["tsys"]
    tcal = metadata["tcal"]
    cal_pwr = metadata["cal_pwr"]
    vslr = metadata["vslr"]
    glat = metadata["glat"]
    glon = metadata["glon"]
    soutrack = metadata["soutrack"]
    bsw = metadata["bsw"]
    return (
        motor_az,
        motor_el,
        freq / pow(10, 6),
        samp_rate / pow(10, 6),
        num_integrations,
        num_bins,
        tsys,
        tcal,
        cal_pwr,
        vslr,
        glat,
        glon,
        soutrack,
        bsw,
    )


class blk(
    gr.sync_block
):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(
        self, directory=".", filename="test.rad", vec_length=4096
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
        self.obsn = 0

    def work(self, input_items, output_items):
        """example: multiply with constant"""
        file = open(pathlib.Path(self.directory, self.filename), "a+")
        tags = self.get_tags_in_window(0, 0, len(input_items[0]))
        latest_data_dict = {
            pmt.to_python(tag.key): pmt.to_python(tag.value) for tag in tags
        }
        yr, da, hr, mn, sc = parse_time(latest_data_dict["rx_time"])
        (
            aznow,
            elnow,
            freq,
            bw,
            integ,
            nfreq,
            tsys,
            tcal,
            calpwr,
            vlsr,
            glat,
            glon,
            soutrack,
            bsw,
        ) = parse_metadata(latest_data_dict["metadata"])
        fbw = bw  # Old SRT Software Had Relative Bandwidth Limits and An Unchanging Sample Rate
        f1 = 0  # Relative Lower Bound (Since Sample Rate Determines Bandwidth)
        f2 = 1  # Relative Upper Bound (Since Sample Rate Determines Bandwidth)
        istart = f1 * nfreq + 0.5
        istop = f2 * nfreq + 0.5
        efflofreq = freq - bw * 0.5
        freqsep = bw / nfreq
        nsam = nfreq  # Old SRT Software Had a Specific Bundle of Samples Shuffled Out and Processed at a Time
        sigma = tsys / sqrt((nsam * integ / (2.0e6 * bw)) * freqsep * 1e6)
        for input_array in input_items[0]:
            p = np.sum(input_array)
            a = len(input_array)
            pwr = (tsys + tcal) * p / (a * calpwr)
            ppwr = pwr - tsys
            header_line = header_format % (
                yr,
                da,
                hr,
                mn,
                sc,
                self.obsn,
                aznow,
                elnow,
                freq,
                tsys,
                ppwr,
                vlsr,
                glat,
                glon,
                soutrack,
            )
            start_line = start_format % (
                istart * bw / nfreq + efflofreq,
                istop * bw / nfreq + efflofreq,
                freqsep,
                bw,
                fbw,
                nfreq,
                nsam,
                istop - istart,
                integ * nsam / (2.0e6 * bw),
                sigma,
                bsw,
            )
            integration_line = integration_format % integ
            file.writelines([header_line, start_line, integration_line])
            for val in input_array:
                file.write(number_format % val)
            file.write("\n")
            self.obsn += 1

        file.close()
        return len(input_items[0])
