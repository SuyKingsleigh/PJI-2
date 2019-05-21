import socket
import sys
import time
from threading import Thread

from Public import *
from mover import Mover
from manual import Manual

from automatico import Automatico


class Robo(Thread):
    """essa classe eh para ser executada no robo, a unica coisa que essa classe faz
    eh mover o robo, e deu"""

    def __init__(self, ip, port, coord_inicial):
        super().__init__()
        # self.socket = socket.socket()
        self.port = port
        self.ip = ip
        self.coord_inicial = coord_inicial
        self.manual = True

        self.map = []
        self.flags = []

        try:
            self.motor = Manual((self.coord_inicial[0], self.coord_inicial[1]))
            print("motor connected")
        except Exception as e:
            print("failled to connect motor", e)

    def _process_data(self, msg):
        # print(msg)
        if msg.cmd == Mover.FRENTE:
            print("frente")
            try:
                self.motor.move(Mover.FRENTE)
            except Exception as e:
                pass
            self.connection.send("200".encode())

        elif msg.cmd == Mover.TRAS:
            print("tras")
            try:
                self.motor.move(Mover.TRAS)
            except Exception as e:
                pass
            self.connection.send("200".encode())

        elif msg.cmd == Mover.DIREITA:
            print("direita")
            try:
                self.motor.move(Mover.DIREITA)
            except Exception as e:
                pass
            self.connection.send("200".encode())

        elif msg.cmd == Mover.ESQUERDA:
            print("esquerda")
            try:
                self.motor.move(Mover.ESQUERDA)
            except Exception as e:
                pass
            self.connection.send("200".encode())

        elif msg == Commands.QUIT:
            self.join()
            self.socket.close()

        elif not msg:
            time.sleep(1)

        elif msg.cmd == Commands.UPDATE_MAP:
            print("mapa: ", msg.data)
            self.map = msg.data

        elif msg.cmd == Commands.UPDATE_FLAGS:
            print("bandeiras: ", msg.data)
            self.flags = msg.data

        else:
            pass
            # time.sleep(0.5)

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
                msg = self.connection.recv(2048)
                msg = Message(None, msg)
                self._process_data(msg)
            except Exception as e:
                print(e)

    def run(self):
        self._connect()
        self._handle()


if __name__ == "__main__":
    """PARAMETROS PARA TESTE EM LOCALHOST 
    localhost 0 0"""
    port = 42069
    # print(sys.argv)
    # ip = sys.argv[1]
    coord = sys.argv[1], sys.argv[2]
    # coord = 0,0
    Robo("0.0.0.0", port, coord).run()

    # lsof -t -i:42069
