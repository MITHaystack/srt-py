"""functions.py

Extra Functions Condensed for Ease-of-Use

"""


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
