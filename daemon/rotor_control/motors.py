"""motors.py

Module for Controlling Different Motor Types over Serial

"""
import serial

from abc import ABC, abstractmethod
from time import sleep


class Motor(ABC):
    """Abstract Class for All Motors Types

    Attributes
    ----------
    port : str
        Serial Port Identifier String for Communicating with the Motor
    az_limits : (float, float)
        Tuple of Lower and Upper Azimuth Limits
    el_limits : (float, float)
        Tuple of Lower and Upper Elevation Limits
    serial : serial.Serial
        Serial Object for Communicating with the Motor

    See Also
    --------
    <https://pyserial.readthedocs.io/en/latest/pyserial_api.html>
    """

    def __init__(self, port, az_limits, el_limits):
        """Constructor for the Abstract Motor Class

        Parameters
        ----------
        port : str
            Serial Port Identifier String for Communicating with the Motor
        az_limits : (float, float)
            Tuple of Lower and Upper Azimuth Limits
        el_limits : (float, float)
            Tuple of Lower and Upper Elevation Limits
        """
        self.port = port
        self.az_limits = az_limits
        self.el_limits = el_limits
        self.serial = None

    @abstractmethod
    def point(self, az, el):
        """Abstract Method Prototype for Pointing a Motor at an AzEl Coordinate

        Parameters
        ----------
        az : float
            Azimuth Coordinate Value to Point At
        el : float
            Elevation Coordinate Value to Point At

        Returns
        -------
        (float, float)
            Azimuth and Elevation Coordinate as a Tuple of Floats
        """
        pass

    @abstractmethod
    def status(self):
        """Abstract Method Prototype for Getting a Motor's Current AzEl Position

        Returns
        -------
        (float, float)
            Azimuth and Elevation Coordinate as a Tuple of Floats
        """
        pass

    def __del__(self):
        """Override of Motor Delete Method to Close Serial Port if Necessary

        Returns
        -------
        None
        """
        if self.serial is not None and self.serial.is_open():
            self.serial.close()


class Rot2Motor(Motor):
    """Class for Controlling any ROT2 Protocol-Supporting Motor (e.g. SPID Motors)

    See Also
    --------
    <http://ryeng.name/blog/3>
    <https://github.com/jaidenfe/rot2proG/blob/master/rot2proG.py>
    <https://www.haystack.mit.edu/edu/undergrad/srt/pdf%20files/MD-01%20en.pdf>
    """

    VALID_PULSES_PER_DEGREE = (1, 2, 4)

    def __init__(self, port, az_limits, el_limits, pulses_per_degree=2):
        """Initializer for Rot2Motor

        Parameters
        ----------
        port : str
            Serial Port Identifier String for Communicating with the Motor
        az_limits : (float, float)
            Tuple of Lower and Upper Azimuth Limits
        el_limits : (float, float)
            Tuple of Lower and Upper Elevation Limits
        pulses_per_degree : int
            Number of Motor Pulses per Degree of Movement
        """
        Motor.__init__(self, port, az_limits, el_limits)
        self.serial = serial.Serial(
            port=self.port,
            baudrate=600,
            bytesize=serial.EIGHTBITS,
            parity="N",
            stopbits=serial.STOPBITS_ONE,
            timeout=None,
        )
        if pulses_per_degree in Rot2Motor.VALID_PULSES_PER_DEGREE:
            self.pulses_per_degree = pulses_per_degree
        else:
            raise ValueError("Invalid Pulse Per Degree Value")

    def send_rot2_pkt(self, cmd, az=None, el=None):
        """Builds and Sends a ROT2 Command Packet over Serial

        Parameters
        ----------
        cmd : int
            ROT2 Motor Command Value (0x2F -> Set, 0x1F -> Get, 0x0F -> Stop)
        az : float
            Azimuth Coordinate to Point At (If Applicable)
        el : float
            Elevation Coordinate to Point At (If Applicable)

        Notes
        -----
        All send_rot2_pkt calls should be followed with a receive_rot2_pkt

        Returns
        -------
        None
        """
        if az is not None and el is not None:
            azimuth = int(
                self.pulses_per_degree * (az + 360.0) + 0.5
            )  # Formatted Az Pulse Value
            elevation = int(
                self.pulses_per_degree * (el + 360.0) + 0.5
            )  # Formatted El Pulse Value
        else:
            azimuth = 0
            elevation = 0

        azimuth_ticks = (
            self.pulses_per_degree
        )  # Documentation for Rot2 Says This Is Ignored
        elevation_ticks = (
            self.pulses_per_degree
        )  # Documentation for Rot2 Says This Is Ignored

        cmd_string = "W%04d%c%04d%c%c " % (
            azimuth,
            azimuth_ticks,
            elevation,
            elevation_ticks,
            cmd,
        )
        cmd_bytes = cmd_string.encode("ascii")
        print("Packet of Size " + str(len(cmd_bytes)))  # TODO: Remove
        print([hex(val) for val in cmd_bytes])  # TODO: Remove
        self.serial.write(cmd_bytes)

    def receive_rot2_pkt(self):
        """Receives and Parsers an ROT2 Status Packet

        Returns
        -------
        (float, float)
            Azimuth and Elevation Coordinate as a Tuple of Floats
        """
        received_bytes = self.serial.read(12)
        received_vals = [ord(val) for val in received_bytes]
        az = (
            (received_vals[1] * 100)
            + (received_vals[2] * 10)
            + received_vals[3]
            + (received_vals[4] / 10.0)
            - 360.0
        )
        el = (
            (received_vals[6] * 100)
            + (received_vals[7] * 10)
            + received_vals[8]
            + (received_vals[9] / 10.0)
            - 360.0
        )
        az_pulse_per_deg = received_vals[5]
        el_pulse_per_deg = received_vals[10]
        assert az_pulse_per_deg == el_pulse_per_deg  # Consistency Check
        if az_pulse_per_deg != self.pulses_per_degree:
            print(
                "Motor Pulses Per Degree Incorrect, Changing Value to "
                + str(az_pulse_per_deg)
            )
            self.pulses_per_degree = az_pulse_per_deg
        return az, el

    def point(self, az, el):
        """Point ROT2 Motor at AzEl Coordinate

        Parameters
        ----------
        az : float
            Azimuth Coordinate to Point At
        el : float
            Elevation Coordinate to Point At

        Returns
        -------
        (float, float)
            Current Azimuth and Elevation Coordinate as a Tuple of Floats
        """
        cmd = 0x2F  # Rot2 Set Command
        self.send_rot2_pkt(cmd, az=az, el=el)
        returned_vals = self.receive_rot2_pkt()
        return returned_vals

    def status(self):
        """Requests the Current Location of the ROT2 Motor

        Returns
        -------
        (float, float)
            Current Azimuth and Elevation Coordinate as a Tuple of Floats
        """
        cmd = 0x1F  # Rot2 Status Command
        self.send_rot2_pkt(cmd)
        returned_vals = self.receive_rot2_pkt()
        return returned_vals

    def stop(self):
        """Stops the ROT2 Motor at its Current Location

        Returns
        -------
        (float, float)
            Current Azimuth and Elevation Coordinate as a Tuple of Floats
        """
        cmd = 0x0F  # Rot2 Stop Command
        self.send_rot2_pkt(cmd)
        returned_vals = self.receive_rot2_pkt()
        return returned_vals


class H180Motor(Motor):
    """
    Class for Controlling any ROT2 Protocol-Supporting Motor (e.g. SPID Motors)
    """

    AZCOUNTS_PER_DEG = 52.0 * 27.0 / 120.0
    ELCOUNTS_PER_DEG = 52.0 * 27.0 / 120.0

    def __init__(self, port, az_limits, el_limits, counts_per_step=100):
        """

        Parameters
        ----------
        port
        """
        Motor.__init__(self, port, az_limits, el_limits)
        self.serial = serial.Serial(
            port=port,
            baudrate=2400,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=None,
        )
        self.count_per_step = counts_per_step
        self.az_lower_lim = az_limits[0]
        self.el_lower_lim = el_limits[0]
        self.az_count = 0.0
        self.el_count = 0.0

    def send_h180_cmd(self, az, el, stow):
        """

        Parameters
        ----------


        Returns
        -------

        """
        azz = az - self.az_lower_lim
        ell = el - self.el_lower_lim
        for axis in range(2):
            mm = -1
            count = 0
            if stow:
                if axis == 0:
                    mm = 0
                else:
                    mm = 2
                count = 8000
            else:
                if axis == 0:
                    acount = azz * H180Motor.AZCOUNTS_PER_DEG - self.az_count
                    if self.count_per_step and acount > self.count_per_step:
                        acount = self.count_per_step
                    if self.count_per_step and acount < -self.count_per_step:
                        acount = -self.count_per_step
                    if acount > 0:
                        count = acount + 0.5
                    else:
                        count = acount - 0.5
                    if count > 0:
                        mm = 1
                    if count < 0:
                        mm = 0
                if axis == 1:
                    acount = ell * H180Motor.ELCOUNTS_PER_DEG - self.el_count
                    if self.count_per_step and acount > self.count_per_step:
                        acount = self.count_per_step
                    if self.count_per_step and acount < -self.count_per_step:
                        acount = -self.count_per_step
                    if acount > 0:
                        count = acount + 0.5
                    else:
                        count = acount - 0.5
                    if count > 0:
                        mm = 3
                    if count < 0:
                        mm = 2
                if count < 0:
                    count = -count
            if mm >= 0 and count:
                cmd_string = " move %d %d%1c" % (mm, count, 13)
                self.serial.write(cmd_string.encode("ascii"))
                resp = ""
                sleep(0.01)
                im = 0
                i = 0
                while i < 32:
                    ch = int.from_bytes(self.serial.read(1), byteorder="big")
                    sleep(0.01)
                    if i < 32:
                        resp += chr(ch)
                        i += 1
                    if ch == 13 or ch == 10:
                        break
                status = i
                sleep(0.1)
                for i in range(status):
                    if resp[i] == "M" or resp[i] == "T":
                        im = i
                ccount = int(resp[im:status].split(" ")[-1])
                if resp[im] == "M":
                    if mm == 1:
                        self.az_count += ccount
                    if mm == 0:
                        self.az_count -= ccount
                    if mm == 3:
                        self.el_count += ccount
                    if mm == 2:
                        self.el_count -= ccount
                if resp[im] == "T":
                    if mm == 1:
                        self.az_count += count
                    if mm == 0:
                        self.az_count -= count
                    if mm == 3:
                        self.el_count += count
                    if mm == 2:
                        self.el_count -= count
        if stow:
            self.az_count = 0
            self.el_count = 0

    def point(self, az, el):
        """

        Parameters
        ----------
        az
        el

        Returns
        -------

        """
        self.send_h180_cmd(az, el, False)
        return self.status()

    def status(self):
        """

        Returns
        -------

        """
        azz = self.az_count / H180Motor.AZCOUNTS_PER_DEG
        ell = self.el_count / H180Motor.ELCOUNTS_PER_DEG
        az = azz + self.az_lower_lim
        el = ell + self.el_lower_lim
        return az, el


class PushRodMotor(Motor):  # TODO: Ask About the Necessary Pushrod Parameters
    """

    """

    AZCOUNTS_PER_DEG = 8.0 * 32.0 * 60.0 / (360.0 * 9.0)

    def __init__(self, port, az_limits, el_limits):
        """

        Parameters
        ----------
        port
        """
        Motor.__init__(self, port, az_limits, el_limits)
        self.serial = serial.Serial(
            port=port,
            baudrate=2400,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=None,
        )

    def point(self, az, el):
        """

        Parameters
        ----------
        az
        el

        Returns
        -------

        """
        pass

    def status(self):
        """

        Returns
        -------

        """
        pass
