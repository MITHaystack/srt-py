import zmq
import numpy as np
from threading import Thread
from time import sleep

import matplotlib.pyplot as plt


class RadioThread(Thread):
    def __init__(
        self, group=None, target=None, name=None, port=5555, cache_size=4_000_000
    ):
        super().__init__(group=group, target=target, name=name, daemon=True)
        self.history = np.zeros(cache_size, dtype="complex64")
        self.history_index = 0
        self.port = port

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:%s" % self.port)
        socket.subscribe("")
        while True:
            rec = socket.recv()
            var = np.frombuffer(rec, dtype="complex64")
            new_history_index = self.history_index + len(var)
            self.history.put(
                range(self.history_index, new_history_index), var, mode="wrap"
            )
            self.history_index = new_history_index % len(self.history)

    def get_sample_history(self, num_samples=-1):
        if 0 < num_samples < len(self.history):
            return self.history.take(
                range(self.history_index, self.history_index + num_samples), mode="wrap"
            )
        return self.history.take(
            range(self.history_index, self.history_index + len(self.history)),
            mode="wrap",
        )


if __name__ == "__main__":
    thread = RadioThread()
    thread.start()
    for _ in range(5):
        sleep(1)
        powerSpectrum, freqenciesFound, time, imageAxis = plt.specgram(
            thread.get_sample_history(), Fc=100000000, Fs=2000000
        )
        plt.xlabel("Time")
        plt.ylabel("Frequency")
        plt.show()
