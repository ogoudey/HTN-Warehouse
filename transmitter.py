import socket
import threading
import time
import math

HOST = '127.0.0.1'
PORT = 5007

class ThroughMessage(threading.Thread):
    def __init__(self, shared):
        super().__init__()
        self.lock = threading.Lock()
        self.shared = shared

    def run(self):
        while True:
            try:
                while True:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((HOST, PORT))
                        with self.lock:
                            message = self.shared["target_message"]
                            s.sendall(message.encode('utf-8'))
            except ConnectionRefusedError:
                print(f"Socket {HOST}:{PORT} is down.")
                time.sleep(2)