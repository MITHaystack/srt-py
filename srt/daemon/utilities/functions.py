"""functions.py

Extra Functions Condensed for Ease-of-Use

"""
import zmq
import numpy as np
from math import isqrt


def angle_within_range(actual_angle, desired_angle, bounds=0.5):
    """Determines if Angles are Within a Threshold of One Another

    Parameters
    ----------
    actual_angle : float
        Value of the Actual Current Angle
    desired_angle : float
        Value of the Desired Angel
    bounds : float
        Maximum Difference Between Actual and Desired Tolerated

    Returns
    -------
    bool
        Whether Angles Were Within Threshold
    """
    return abs(actual_angle - desired_angle) < bounds


def azel_within_range(actual_azel, desired_azel, bounds=(0.5, 0.5)):
    """Determines if AzEls are Within a Threshold of One Another

    Parameters
    ----------
    actual_azel : (float, float)
        Value of the Actual Current Azimuth and Elevation
    desired_azel : (float, float)
        Value of the Desired Azimuth and Elevation
    bounds : (float, float)
        Maximum Difference Between Actual and Desired Tolerated
    Returns
    -------
    bool
        Whether Angles Were Within Threshold
    """
    actual_az, actual_el = actual_azel
    desired_az, desired_el = desired_azel
    bounds_az, bounds_el = bounds
    return angle_within_range(actual_az, desired_az, bounds_az) and angle_within_range(
        actual_el, desired_el, bounds_el
    )


def get_spectrum(port=5561):
    """Quickly opens a zmq socket and gets a spectrum

    Parameters
    ----------
    port : int
        Number that the spectrum data is broadcast on.

    Returns
    -------
    var : array_like
        Spectrum array as numpy array

    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:%s" % port)
    socket.subscribe("")
    try:
        rec = socket.recv()
        var = np.frombuffer(rec, dtype="float32")
    except:
        return None

    return var


def sinc_interp2d(x, y, values, dx, dy, xout, yout):
    """Perform a sinc interpolation

    Parameters
    ----------
    x : array_like
        A 1-d array of x values.
    y : array_like
        A 1-d array of y values.
    values : array_like
        A 1-d array of values that will be interpolated.
    dx : float
        Sampling rate along the x axis.
    dy : float
        Sampling rate along the y axis.
    xout : array_like
        2-d array for x axis sampling.
    yout : array_like
        2-d array for y axis sampling.

    Returns
    -------
    val_out : array_like
        2-d array for of the values at the new sampling sampling.
    """

    val_out = np.zeros_like(xout)

    for x_c, y_c, v_c in zip(x, y, values):
        x_1 = (xout - x_c) / dx
        y_1 = (yout - y_c) / dy
        val_out += float(v_c) * np.sinc(x_1) * np.sinc(y_1)

    return val_out


def npoint_interp(az, el, val, d_az, d_el, nout=100):
    """Interpolate the result of the npoint scan on to a grid.

    Parameters
    ----------
    az : array_like
        A 1-d array of az values.
    el : array_like
        A 1-d array of el values.
    val : array_like
        A 1-d array of values that will be interpolated.
    d_az : float
        Sampling rate along the az axis.
    d_el : float
        Sampling rate along the el axis.
    nout : int
        Number of samples per axis.

    Returns
    -------
    azarr : array_like
        2-d array for az axis sampling.
    elarr : array_like
        2-d array for el axis sampling.
    val_out : array_like
        2-d array for of the values at the new sampling sampling.
    """

    azmin = np.nanmin(az)
    azmax = np.nanmax(az)
    azvec = np.linspace(azmin, azmax, nout)

    elmin = np.nanmin(el)
    elmax = np.nanmax(el)
    elvec = np.linspace(elmin, elmax, nout)
    azarr, elarr = np.meshgrid(azvec, elvec, indexing="xy")

    val_out = sinc_interp2d(
        az, el, val, d_az, d_el, azarr.astype(float), elarr.astype(float)
    )

    return azarr, elarr, val_out


def is_square(i: int) -> bool:
    """Check if input is a square of nautral number

    Parameters
    ----------
    i : int
        Number to chceck

    Returns
    -------
    bool
        If input is a square of nautral number

    """
    return i == isqrt(i) ** 2