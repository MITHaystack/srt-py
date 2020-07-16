"""rotors.py

Module for Managing Different Motor Objects

"""
from enum import Enum

from rotor_control.motors import NoMotor, Rot2Motor, H180Motor, PushRodMotor


def angle_within_range(angle, limits):
    lower_limit, upper_limit = limits
    if lower_limit <= upper_limit:
        return lower_limit <= angle <= upper_limit
    else:
        return not lower_limit < angle < upper_limit


class RotorType(Enum):
    """
    Enum Class for the Different Types of
    """

    NONE = "NONE"
    ROT2 = "ALFASPID"
    H180 = "H180MOUNT"
    PUSH_ROD = "PUSHROD"


class Rotor:
    """
    Class for Controlling Any Rotor Motor Through a Common Interface

    See Also
    --------
    motors.py
    """

    def __init__(self, motor_type, port, az_limits, el_limits, az_offset, el_offset):
        """Initializes the Rotor with its Motor Object

        Parameters
        ----------
        motor_type : RotorType
            String enum Identifying the Type of Motor
        port : str
            Serial Port Identifier String for Communicating with the Motor
        az_limits : (float, float)
            Tuple of Lower and Upper Azimuth Limits
        el_limits : (float, float)
            Tuple of Lower and Upper Elevation Limits
        """
        if motor_type == RotorType.NONE or motor_type == RotorType.NONE.value:
            self.motor = NoMotor(port, az_limits, el_limits)
        elif motor_type == RotorType.ROT2 or motor_type == RotorType.ROT2.value:
            self.motor = Rot2Motor(port, az_limits, el_limits)
        elif motor_type == RotorType.H180 or motor_type == RotorType.H180.value:
            self.motor = H180Motor(port, az_limits, el_limits)
        elif motor_type == RotorType.PUSH_ROD == RotorType.PUSH_ROD.value:
            self.motor = PushRodMotor(port, az_limits, el_limits)
        else:
            raise ValueError("Not a known motor type")

        self.az_limits = az_limits
        self.el_limits = el_limits
        self.az_offset = az_offset
        self.el_offset = el_offset

    def get_azimuth_elevation(self):
        """Latest Known Azimuth and Elevation

        Returns
        -------
        (float, float)
            Azimuth and Elevation Coordinate as a Tuple of Floats
        """
        azz, ell = self.motor.status()
        az = (azz + self.az_offset + 360) % 360
        el = ell + self.el_offset
        return az, el

    def set_azimuth_elevation(self, az, el):
        """Sets the Azimuth and Elevation of the Motor

        Parameters
        ----------
        az : float
            Azimuth Coordinate to Point At
        el : float
            Elevation Coordinate to Point At

        Returns
        -------
        None
        """
        if angle_within_range(az, self.az_limits) and angle_within_range(el, self.el_limits):
            azz = (az - self.az_offset + 360) % 360
            ell = el - self.el_offset
            self.motor.point(azz, ell)
        else:
            raise ValueError("Angle Not Within Bounds")
