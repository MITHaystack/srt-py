"""raw_radio_fetcher.py

Thread Which Handles Receiving Raw I/Q Samples

"""

import zmq
import numpy as np
from threading import Thread
from time import sleep


class RadioThread(Thread):
    """
    Thread for Fetching Raw I/Q Samples from GNU Radio via ZMQ PUB/SUB
    """

    def __init__(
        self, group=None, target=None, name=None, port=5559, cache_size=4_000_000
    ):
        """Initializer for the RadioThread

        Parameters
        ----------
        group : NoneType
            The ThreadGroup the Thread Belongs to (Currently Unimplemented in Python 3.8)
        target : callable
            Function that the Thread Should Run (Leave This Be For Command Sending)
        name : str
            Name of the Thread
        port : int
            Port of the Raw I/Q Sample ZMQ PUB/SUB Socket
        cache_size : int
            Number of Samples to Keep In Cache
        """
        super().__init__(group=group, target=target, name=name, daemon=True)
        self.history = np.zeros(cache_size, dtype="complex64")
        self.history_index = 0
        self.port = port

    def run(self):
        """Grabs Samples From ZMQ, Converts them to Numpy, and Stores

        Returns
        -------
        None
        """
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:%s" % self.port)
        socket.subscribe("")
        while True:
            rec = socket.recv()
            print(len(rec))
            var = np.frombuffer(rec, dtype="complex64")
            new_history_index = self.history_index + len(var)
            self.history.put(
                range(self.history_index, new_history_index), var, mode="wrap"
            )
            self.history_index = new_history_index % len(self.history)

    def get_sample_history(self, num_samples=-1):
        """Get a Copy of the Sample History

        Parameters
        ----------
        num_samples : int
            Number of Samples to Return in an Array ; If -1, then Return All

        Returns
        -------
        A Portion of the Sample History : (num_samples) ndarray
        """
        if 0 < num_samples < len(self.history):
            return self.history.take(
                range(self.history_index, self.history_index + num_samples), mode="wrap"
            )
        return self.history.take(
            range(self.history_index, self.history_index + len(self.history)),
            mode="wrap",
        )


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    thread = RadioThread()
    thread.start()
    sleep(1)
    powerSpectrum, freqenciesFound, time, imageAxis = plt.specgram(
        thread.get_sample_history(), Fc=100000000, Fs=2000000
    )
    plt.xlabel("Time")
    plt.ylabel("Frequency")
    plt.show()
