import socket
from sys import argv
import threading
from game import *


class Server:
    def __init__(self, sock):
        self.sock = sock
        self.threads = []
        self.running = False
        self.game = Game()

    def run(self):
        self.running = True
        self.game.playing = True
        self.sock.listen(5)
        while self.running:
            new_soc, cs = self.sock.accept()
            t = threading.Thread(None, self.game.start_player, None, args=(new_soc,))
            self.threads.append(t)
            t.start()

        self.shutdown()

    def shutdown(self):
        self.running = False
        self.game.playing = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            for t in self.threads:
                t.join()

        except:
            pass


if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 5555
    if len(argv) > 1:
        port = int(argv[1])

    s.bind(("", port))
    server = Server(s)
    try:
        server.run()

    except:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        server.shutdown()
