"""galactic_rotation_curve.py

Example Script for Loading Output of Galactic Rotation Curve Experiment from FITS
Assumes that the experiment has already been run and files are in local folder
 - Point at G00 through G90 and record for several minutes at each into files g00-g90.fits
 - The command script used for this test was developed by Dahlia Dry for srt-labs

"""

from matplotlib import pyplot as plt
from astropy.io import fits
import numpy as np
import json

for val in range(0, 100, 10):
    hdul = fits.open(f"./g{str(val).zfill(2)}.fits")
    averaged = np.zeros(len(hdul[0].data))
    num = 0
    for hdu in hdul:
        averaged += hdu.data
        num += 1
    averaged /= num

    metadata = json.loads(hdul[0].header["METADATA"])
    num_bins = metadata["num_bins"]
    samp_rate = metadata["samp_rate"]
    center_freq = metadata["freq"]

    subsample_factor = 1
    averaged_subsampled = np.zeros(num_bins//subsample_factor)
    for i, val in enumerate(averaged):
        averaged_subsampled[i//subsample_factor] += val
    averaged_subsampled /= subsample_factor

    lower_bound = int(round(0 * len(averaged_subsampled)))
    upper_bound = int(round(1.0 * len(averaged_subsampled)))

    bins = np.linspace(-samp_rate / 2, samp_rate / 2, len(averaged_subsampled)) + center_freq - 0.05 * pow(10, 6)
    averaged_subsampled = averaged_subsampled[lower_bound: upper_bound]
    averaged_subsampled -= np.min(averaged_subsampled)
    bins = bins[lower_bound: upper_bound]

    plt.hist(bins, weights=averaged_subsampled, bins=len(bins))
    plt.show()
