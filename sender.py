import socket
import json
from config import UDP_HOST, UDP_PORT, PLAYER_ID, BOSS_ID

class GestureSender:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = (UDP_HOST, UDP_PORT)

    def send(self,player_id, gesture: str):
        """Send a small JSON packet to the SFML game."""
        payload = json.dumps({
            
            'player': player_id,        # 1 for player, 0 for boss
            'gesture': gesture,       # e.g. "ATTACK"
        }).encode('utf-8')
        try:
            self.sock.sendto(payload, self.addr)
        except OSError as e:
            print(f"[sender] socket error: {e}")

    def close(self):
        self.sock.close()