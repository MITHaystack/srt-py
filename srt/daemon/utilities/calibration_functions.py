"""calibration_functions.py

dsheen 2024/09/18
Calibration Mathhematics for new SRT calibration scheme

reimplements basic cold sky cal implemented directly in gnuradio 
and adds additional capabilities for more advanced telescopes.
"""

import numpy as np
import numpy.polynomial.polynomial as poly
from astropy.io import fits

def get_averaged_spectrum(fits_file):
    """
    open fits file and average all included spectra together
    """
    spectrum_file = fits.open(fits_file)
    average_spectrum = np.zeros(len(spectrum_file[0].data),dtype=np.float64)

    num_spectra = len(spectrum_file)
    for i in range(0,num_spectra):
        spectrum=spectrum_file[i]
        average_spectrum += spectrum.data

    average_spectrum /= num_spectra

    return average_spectrum


def basic_cold_sky_calibration_fit(cold_sky_reference_filepath, t_sys=300, t_cal=300, polynomial_order=20):
    """
    very basic calibration for single point temperature reference measurement. 
    calculates a polynomial fit for the spectrum and appropriately normalizes it
    """

    average_cold_sky_spectrum = get_averaged_spectrum(cold_sky_reference_filepath)
    relative_freq_values = np.linspace(-1, 1, len(average_cold_sky_spectrum))
    polynomial_fit = poly.Polynomial.fit(relative_freq_values, average_cold_sky_spectrum, polynomial_order,)

    smoothed_cold_sky_spectrum = polynomial_fit(relative_freq_values)
    average_value = np.average(smoothed_cold_sky_spectrum)
    normalized_gain_spectrum = smoothed_cold_sky_spectrum/average_value
    average_gain_correction = average_value/(t_sys+t_cal)


    return normalized_gain_spectrum, average_gain_correction

    
def additive_noise_calibration_fit(cold_sky_reference_filepath, calibrator_reference_filepath, t_sys=300, t_cal=300, polynomial_order=20):

    average_cold_sky_spectrum = get_averaged_spectrum(cold_sky_reference_filepath)
    average_calibrator_plus_sky_spectrum = get_averaged_spectrum(calibrator_reference_filepath)
    average_calibrator_spectrum = average_calibrator_plus_sky_spectrum - average_cold_sky_spectrum

    relative_freq_values = np.linspace(-1, 1, len(average_cold_sky_spectrum))
    polynomial_fit = poly.Polynomial.fit(relative_freq_values, average_calibrator_spectrum, polynomial_order,)

    smoothed_calibrator_spectrum = polynomial_fit(relative_freq_values)
    average_value = np.average(smoothed_calibrator_spectrum)
    normalized_gain_spectrum = smoothed_calibrator_spectrum/average_value
    average_gain_correction = average_value/t_cal

    return normalized_gain_spectrum, average_gain_correction








