# state_receiver.py
import socket
import json

class StateReceiver:
    def __init__(self, host='127.0.0.1', port=5006):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.sock.setblocking(False)
        self._state = {
            'player': {'x': 0, 'y': 0, 'action': 'IDLE', 'hp': 100},
            'enemy':  {'x': 0, 'y': 0, 'action': 'IDLE', 'hp': 100},
        }

    def update(self):
        """Drain all pending packets, keep only the latest."""
        try:
            while True:
                data, _ = self.sock.recvfrom(1024)
                self._state = json.loads(data.decode('utf-8'))
        except BlockingIOError:
            pass

    def get_player(self):
        return self._state['player']

    def get_enemy(self):
        return self._state['enemy']

    def get(self):
        return self._state

    def close(self):
        self.sock.close()