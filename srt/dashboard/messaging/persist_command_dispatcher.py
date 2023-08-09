"""persist_command_dispatcher.py

Thread Which Handles Sending Commands to the Observations Persist Queue

"""

import zmq
from threading import Thread
from queue import Queue


class PersistQueueThread(Thread):
    """
    Thread Which Handles Sending Commands to the Observations Persist Queue
    """

    def __init__(self, group=None, target=None, name=None, queue_path=None):
        """Initializer for the Observations Persist Queue Thread

        Parameters
        ----------
        group : NoneType
            The ThreadGroup the Thread Belongs to (Currently Unimplemented in Python 3.8)
        target : callable
            Function that the Thread Should Run (Leave This Be For Command Sending)
        name : str
            Name of the Thread
        queue_path : str
            path to the persist queue database
        """
        super().__init__(group=group, target=target, name=name, daemon=True)
        self.queue = Queue()
        #TODO initialization

    def run(self):
        """Grabs Commands from the Queue and Sends the to the Observations Persist Queue

        Returns
        -------
        None
        """
    
        while self.is_alive():
            command = self.queue.get()
            #TODO write dict to persist queue

    def add_to_queue(self, cmd):
        """Adds a New Item to the Queue

        Parameters
        ----------
        cmd : str
            New Command to Add to the Queue

        Returns
        -------
        None
        """
        self.queue.put(cmd)

    def get_queue_empty(self):
        """Returns if the Queue is Empty

        Returns
        -------
        bool
            If the Queue is Empty
        """
        return self.queue.empty()