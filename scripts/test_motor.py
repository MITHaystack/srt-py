"""

"""
from random import uniform
from time import sleep

from rotor_control.rotors import Rotor, RotorType

stow_position = (38, 0)  # Taken from Starting Position of Haystack SRT
az_limit = (38, 355)  # Taken From Haystack srt.cat
el_limit = (0, 89)  # Taken From Haystack srt.cat

if __name__ == "__main__":
    rotor = Rotor(RotorType.ROT2, "/dev/ttyUSB0")
    az, el = rotor.get_azimuth_elevation()
    print("Current AzEl: " + str((az, el)))

    num_points = 10
    test_points = (
        (uniform(az_limit[0], az_limit[1]), uniform(el_limit[0], el_limit[1]))
        for _ in range(num_points)
    )

    for point in test_points:
        rotor.set_azimuth_elevation(point[0], point[1])
        while abs(az - point[0]) > 1 or abs(el - point[1]) > 1:
            sleep(1)
            az, el = rotor.get_azimuth_elevation()
            print("Current AzEl: " + str((az, el)))
        print("Point " + str(point) + " Movement Complete")
        sleep(5)

    print("Stowing Dish")
    rotor.set_azimuth_elevation(stow_position[0], stow_position[1])
    while abs(az - stow_position[0]) > 1 or abs(el - stow_position[1]) > 1:
        sleep(1)
        az, el = rotor.get_azimuth_elevation()
        print("Current AzEl: " + str((az, el)))
    print("Stow Complete")
