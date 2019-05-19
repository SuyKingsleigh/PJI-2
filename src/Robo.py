import socket
import sys
from threading import Thread

from Public import Commands
from mover import Mover


class Robo(Thread):
    """essa classe eh para ser executada no robo, a unica coisa que essa classe faz
    eh mover o robo, e deu"""
    def __init__(self, ip, port, coord_inicial):
        super().__init__()
        # self.socket = socket.socket()
        self.port = port
        self.ip = ip
        self.coord_inicial = coord_inicial
        try: self.motor = Mover(self.coord_inicial[0],self.coord_inicial[1])
        except Exception as e: pass

    def _process_data(self, msg):
        print(msg)
        if msg == Mover.FRENTE:
            print("frente")
            try: self.motor.move(Mover.FRENTE)
            except Exception as e: pass

        elif msg == Mover.TRAS:
            print("tras")
            try: self.motor.move(Mover.TRAS)
            except Exception as e: pass

        elif msg == Mover.DIREITA:
            print("direita")
            try: self.motor.move(Mover.DIREITA)
            except Exception as e: pass

        elif msg == Mover.ESQUERDA:
            print("esquerda")
            try: self.motor.move(Mover.ESQUERDA)
            except Exception as e: pass

        elif msg == Commands.QUIT:
            self.join()
            self.socket.close()
        else: pass

    def _connect(self):
        """Conecta o robo ao controlador"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)
        self.connection, self.address = self.socket.accept()
        print("conectado com, ", self.address)


    def _handle(self):
        while True:
            try:
                msg = self.connection.recv(256).decode()
                print("msg")
                self._process_data(msg)
            except Exception as e: print(e)

    def run(self):
        self._connect()
        self._handle()


if __name__ == "__main__":
    # print("ip de onde esta sendo executado o SR-Controlador, porta, ")
    port = 42069
    # print(sys.argv)
    ip = sys.argv[1]
    coord = sys.argv[2], sys.argv[3]
    # coord = 0,0
    Robo(ip,port,coord).run()