"""status_fetcher.py

Thread Which Handles Receiving Status Data

"""

import zmq
from threading import Thread
from time import sleep
import json


class StatusThread(Thread):
    """
    Thread Which Handles Receiving Status Data
    """

    def __init__(self, group=None, target=None, name=None, port=5555):
        """Initializer for StatusThread

        Parameters
        ----------
        group : NoneType
            The ThreadGroup the Thread Belongs to (Currently Unimplemented in Python 3.8)
        target : callable
            Function that the Thread Should Run (Leave This Be For Command Sending)
        name : str
            Name of the Thread
        port : int
            Port of the Status Data ZMQ PUB/SUB Socket
        """
        super().__init__(group=group, target=target, name=name, daemon=True)
        self.status = None
        self.port = port

    def run(self):
        """Grabs Most Recent Status From ZMQ and Stores

        Returns
        -------

        """
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:%s" % self.port)
        socket.subscribe("")
        while True:
            rec = socket.recv()
            dump = json.loads(rec)
            self.status = dump

    def get_status(self):
        """Return Most Recent Status Dictionary

        Returns
        -------
        dict
            Status Dictionary
        """
        return self.status


if __name__ == "__main__":
    thread = StatusThread()
    thread.start()
    sleep(1)
    print(thread.get_status())
