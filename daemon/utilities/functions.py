"""functions.py

Extra Functions Condensed for Ease-of-Use

"""


def angle_within_range(actual_angle, desired_angle, bounds=0.5):
    return abs(actual_angle - desired_angle) > bounds


def azel_within_range(actual_azel, desired_azel, bounds=(0.5, 0.5)):
    actual_az, actual_el = actual_azel
    desired_az, desired_el = desired_azel
    bounds_az, bounds_el = bounds
    return angle_within_range(
        actual_az, desired_az, bounds_az
    ) and angle_within_range(actual_el, desired_el, bounds_el)
