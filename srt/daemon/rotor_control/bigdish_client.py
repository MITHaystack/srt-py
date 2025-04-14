#!/usr/bin/env python3

import time
import json
import threading
from websockets.sync.client import connect

class BigDishClient:
    def __init__(self, server_host, server_port, user, password, kick_others = False):
        self.websocket = connect(f"ws://{server_host}:{server_port}")
        self.message_id = 0
        self.websocket.send(json.dumps({"type": "auth", "id": self.message_id, "user": user, "password": password, "version": "0.0.1"}))
        self.message_id += 1
        self.websocket.send(json.dumps({"type": "init", "id": self.message_id, "kick_others": kick_others}))
        self.message_id += 1
        self.received_messages = {}
        self._message_recv_thread_handle = threading.Thread(target = self._message_recv_thread)
        self._message_recv_thread_handle.start()

    def _message_recv_thread(self):
        for message in self.websocket:
            message_decoded = json.loads(message)
            self.received_messages[message_decoded["id"]] = message_decoded

    def _wait_for_response(self, id):
        while True:
            if id in self.received_messages:
                message = self.received_messages[id]
                del self.received_messages[id]
                self.message_id += 1
                return message
            time.sleep(0.01)

    def stow_pos(self):
        self.websocket.send(json.dumps({"type": "stow_pos", "id": self.message_id}))
        return self._wait_for_response(self.message_id)

    def goto_posvel_azel(self, az_pos, el_pos, az_vel, el_vel):
        self.websocket.send(json.dumps({"type": "goto_posvel", "id": self.message_id, "coords": "azel", "az_pos": az_pos, "az_vel": az_vel, "el_pos": el_pos, "el_vel": el_vel}))
        return self._wait_for_response(self.message_id)
    
    def track_radec(self, ra_pos, dec_pos, duration):
        self.websocket.send(json.dumps({"type": "track", "id": self.message_id, "coords": "radec", "ra_pos": ra_pos, "dec_pos": dec_pos, "duration": duration}))
        return self._wait_for_response(self.message_id)

    def track_gal(self, l_pos, b_pos, duration):
        self.websocket.send(json.dumps({"type": "track", "id": self.message_id, "coords": "gal", "l_pos": l_pos, "b_pos": b_pos, "duration": duration}))
        return self._wait_for_response(self.message_id)

    def get_posvel(self, coords, power):
        self.websocket.send(json.dumps({"type": "get_posvel", "id": self.message_id, "coords": coords, "power": power}))
        return self._wait_for_response(self.message_id)

if __name__ == "__main__":
    client = BigDishClient("localhost", 1234, "w1xm", "test", kick_others = True)
    #while True:
    #    client.track_gal(162.592,4.5697, 5)
    #    time.sleep(1)
