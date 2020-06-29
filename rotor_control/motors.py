import serial

from abc import ABC, abstractmethod
from time import sleep


class Motor(ABC):
    """

    """

    def __init__(self, port):
        """

        :param port:
        """
        self.port = port
        self.serial = None

    @abstractmethod
    def point(self, az, el):
        """

        :param az:
        :param el:
        :return:
        """
        pass

    @abstractmethod
    def status(self):
        """

        :return:
        """
        pass

    @abstractmethod
    def stop(self):
        """

        :return:
        """
        pass

    def __del__(self):
        """

        :return:
        """
        if self.serial is not None and self.serial.is_open():
            self.serial.close()


class Rot2Motor(Motor):
    """

    """

    VALID_PULSES_PER_DEGREE = (1, 2, 4)

    def __init__(self, port, pulses_per_degree=2):
        """

        :param port:
        :param pulses_per_degree:
        """
        Motor.__init__(self, port)
        self.serial = serial.Serial(port=self.port, baudrate=600, bytesize=8, parity='N', stopbits=1, timeout=None)
        if pulses_per_degree in Rot2Motor.VALID_PULSES_PER_DEGREE:
            self.pulses_per_degree = pulses_per_degree
        else:
            raise ValueError("Invalid Pulse Per Degree Value")

    def send_rot2_pkt(self, cmd, az=None, el=None):
        """

        :param cmd:
        :param az:
        :param el:
        :return:
        """
        if az is not None and el is not None:
            azimuth = int(self.pulses_per_degree * (az + 360.0) + 0.5)  # Formatted Az Pulse Value
            elevation = int(self.pulses_per_degree * (el + 360.0) + 0.5)  # Formatted El Pulse Value
        else:
            azimuth = 0
            elevation = 0

        azimuth_ticks = self.pulses_per_degree  # Documentation for Rot2 Says This Is Ignored
        elevation_ticks = self.pulses_per_degree  # Documentation for Rot2 Says This Is Ignored

        cmd_string = "W%04d%c%04d%c%c " % (azimuth, azimuth_ticks, elevation, elevation_ticks, cmd)
        cmd_bytes = cmd_string.encode('ascii')
        print("Packet of Size " + str(len(cmd_bytes)))  # TODO: Remove
        print([hex(val) for val in cmd_bytes])  # TODO: Remove
        self.serial.write(cmd_bytes)

    def receive_rot2_pkt(self):
        """

        :return:
        """
        received_bytes = self.serial.read(12)
        received_vals = [ord(val) for val in received_bytes]
        az = (received_vals[1] * 100) + (received_vals[2] * 10) + received_vals[3] + (received_vals[4] / 10.0) - 360.0
        el = (received_vals[6] * 100) + (received_vals[7] * 10) + received_vals[8] + (received_vals[9] / 10.0) - 360.0
        az_pulse_per_deg = received_vals[5]
        el_pulse_per_deg = received_vals[10]
        assert (az_pulse_per_deg == el_pulse_per_deg)  # Consistency Check
        if az_pulse_per_deg != self.pulses_per_degree:
            print("Motor Pulses Per Degree Incorrect, Changing Value to " + str(az_pulse_per_deg))
            self.pulses_per_degree = az_pulse_per_deg
        return az, el

    def point(self, az, el):
        """

        :param az:
        :param el:
        :return:
        """
        cmd = 0x2F  # Rot2 Set Command
        self.send_rot2_pkt(cmd, az=az, el=el)
        returned_vals = self.receive_rot2_pkt()
        return returned_vals

    def status(self):
        """

        :return:
        """
        cmd = 0x1F  # Rot2 Status Command
        self.send_rot2_pkt(cmd)
        returned_vals = self.receive_rot2_pkt()
        return returned_vals

    def stop(self):
        """

        :return:
        """
        cmd = 0x0F  # Rot2 Stop Command
        self.send_rot2_pkt(cmd)
        returned_vals = self.receive_rot2_pkt()
        return returned_vals


class H180Motor(Motor):
    AZCOUNTS_PER_DEG = (52.0 * 27.0 / 120.0)
    ELCOUNTS_PER_DEG = (52.0 * 27.0 / 120.0)

    def __init__(self, port):
        Motor.__init__(self, port)
        self.serial = serial.Serial(port=port, baudrate=2400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE, timeout=None)
        self.az_count = 0.0
        self.el_count = 0.0
        self.count_per_step = 100  # TODO: Is this right/needed?
        self.azcmd = 0
        self.azlim1 = 0
        self.elcmd = 0
        self.ellim1 = 0
        self.stow = 0

    def connect(self, cmd):
        count = 0
        azz = self.azcmd - self.azlim1
        ell = self.elcmd - self.ellim1
        for axis in range(2):
            mm = -1
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
            if self.stow == 1:
                if axis == 0:
                    mm = 0
                else:
                    mm = 2
                count = 8000
            if cmd == 2 and mm >= 0 and count:
                cmd_string = " move %d %d%1c" % (mm, count, 13)
                self.serial.write(cmd_string.encode('ascii'))
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
                    if resp[i] == 'M' or resp[i] == 'T':
                        im = i
                ccount = int(resp[im:status].split(" ")[-1])
                if resp[im] == 'M':
                    if mm == 1:
                        self.az_count += ccount
                    if mm == 0:
                        self.az_count -= ccount
                    if mm == 3:
                        self.el_count += ccount
                    if mm == 2:
                        self.el_count -= ccount
                if resp[im] == 'T':
                    if mm == 1:
                        self.az_count += count
                    if mm == 0:
                        self.az_count -= count
                    if mm == 3:
                        self.el_count += count
                    if mm == 2:
                        self.el_count -= count


    def point(self, az, el):
        pass

    def status(self):
        pass

    def stop(self):
        pass


class PushRodMotor(Motor):
    def __init__(self, port):
        Motor.__init__(self, port)

    def point(self, az, el):
        pass

    def status(self):
        pass

    def stop(self):
        pass
