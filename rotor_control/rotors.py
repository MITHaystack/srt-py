from enum import Enum

from rotor_control.motors import Rot2Motor, H180Motor, PushRodMotor


class RotorType(Enum):
    ROT2 = 'rot2'
    H180 = 'h180'
    PUSH_ROD = 'push_rod'


class Rotor:
    def __init__(self, motor_type, port):
        if motor_type == RotorType.ROT2:
            self.motor = Rot2Motor(port)
        elif motor_type == RotorType.H180:
            self.motor = H180Motor(port)
        elif motor_type == RotorType.PUSH_ROD:
            self.motor = PushRodMotor(port)
        else:
            raise ValueError("Not a known motor type")

    def get_azimuth_elevation(self):
        return self.motor.status()

    def set_azimuth_elevation(self, az, el):
        self.motor.point(az, el)
