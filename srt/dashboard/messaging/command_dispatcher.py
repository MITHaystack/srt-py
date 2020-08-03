import zmq
from threading import Thread
from queue import Queue


class CommandThread(Thread):
    def __init__(self, group=None, target=None, name=None, port=5556):
        super().__init__(group=group, target=target, name=name, daemon=True)
        self.queue = Queue()
        self.port = port

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect("tcp://localhost:%s" % self.port)
        while self.is_alive():
            command = self.queue.get()
            socket.send_string(command)

    def add_to_queue(self, cmd):
        self.queue.put(cmd)

    def get_queue_empty(self):
        return self.queue.empty()


def test_cmd_send():  # TODO: Look into PyTest Fixtures - Having Multiple Threads in PyTest Causes Copious Warnings
    from time import sleep

    port = 5556
    num_dispatchers = 10
    num_in_queue = 5

    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind("tcp://*:%s" % port)

    def receive_func():
        while True:
            received.append(socket.recv_string())

    threads = [CommandThread(port=port) for _ in range(num_dispatchers)]
    for i, thread in enumerate(threads):
        for _ in range(num_in_queue):
            thread.add_to_queue(str(i))
    for thread in threads:
        thread.start()

    received = []
    receive_thread = Thread(target=receive_func, daemon=True)
    receive_thread.start()
    sleep(1)
    print(received)
    assert len(received) == num_in_queue * num_dispatchers
