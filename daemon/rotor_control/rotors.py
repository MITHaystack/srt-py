"""rotors.py

Module for Managing Different Motor Objects

"""
from enum import Enum

from rotor_control.motors import Rot2Motor, H180Motor, PushRodMotor


class RotorType(Enum):
    """
    Enum Class for the Different Types of
    """

    ROT2 = "ALFASPID"
    H180 = "H180Mount"
    PUSH_ROD = "PUSHROD"


class Rotor:
    """
    Class for Controlling Any Rotor Motor Through a Common Interface

    See Also
    --------
    motors.py
    """

    def __init__(self, motor_type, port, az_limits, el_limits):
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
        if motor_type == RotorType.ROT2:
            self.motor = Rot2Motor(port, az_limits, el_limits)
        elif motor_type == RotorType.H180:
            self.motor = H180Motor(port, az_limits, el_limits)
        elif motor_type == RotorType.PUSH_ROD:
            self.motor = PushRodMotor(port, az_limits, el_limits)
        else:
            raise ValueError("Not a known motor type")

    def get_azimuth_elevation(self):
        """Latest Known Azimuth and Elevation

        Returns
        -------
        (float, float)
            Azimuth and Elevation Coordinate as a Tuple of Floats
        """
        return self.motor.status()

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
        self.motor.point(az, el)
