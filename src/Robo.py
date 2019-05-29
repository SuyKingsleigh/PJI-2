import socket
import sys
import time
from threading import Thread

from Public import *
from mover import Mover


class Robo(Thread):
    """essa classe eh para ser executada no robo, a unica coisa que essa classe faz
    eh mover o robo, e eventualmente ativar o modo automatico"""

    def __init__(self, ip, port, coord_inicial):
        super().__init__()
        # self.socket = socket.socket()
        self.port = port
        self.ip = ip
        self.current_pos = coord_inicial
        self.manual = True

        self.map = []
        self.flags = []
        # global flags
        try:
            self.motor = Robo((self.current_pos[0], self.current_pos[1]))
            print("motor connected")
        except Exception as e:
            print("failled to connect motor", e)

    def _process_data(self, msg):
        # print(msg)
        if msg.cmd == Mover.FRENTE:
            print("frente")
            try:
                # self.motor.move(Mover.FRENTE)
                self.frente()
            except Exception as e:
                pass

        elif msg.cmd == Mover.TRAS:
            print("tras")
            try:
                # self.motor.move(Mover.TRAS)
                self.tras()
            except Exception as e:
                pass

        elif msg.cmd == Mover.DIREITA:
            print("direita")
            try:
                # self.motor.move(Mover.DIREITA)
                self.direita()
            except Exception as e:
                pass

        elif msg.cmd == Mover.ESQUERDA:
            print("esquerda")
            try:
                # self.motor.move(Mover.ESQUERDA)
                self.esquerda()
            except Exception as e:
                pass

        elif msg == Commands.QUIT:
            self.join()
            self.socket.close()

        elif not msg:
            time.sleep(1)

        elif msg.cmd == Commands.UPDATE_MAP:
            print("mapa: ", msg.data)
            self.map = msg.data
            global global_map
            global_map = self.map


        elif msg.cmd == Commands.UPDATE_FLAGS:
            print("bandeiras: ", msg.data)
            self.flags = msg.data
            global global_flags
            global_flags = self.flags

        elif msg.cmd == Commands.MODE:
            # automatico = False
            if not msg.data:
                print("Modo automatico\n")
                automatico = Automatico(self)
                self.auto_thread = Thread(target=automatico.run)
                self.auto_thread.daemon = False
                self.auto_thread.start()
            else:
                print("Modo manual\n")
                if self.auto_thread.is_alive(): self.auto_thread.join(timeout=10)


        else:
            pass
            # time.sleep(0.5)

    def frente(self):
        self.motor.move(Mover.FRENTE)
        self.current_pos = int(self.current_pos[0]) + 1, int(self.current_pos[1])
        if not self.manual:
            msg = Message(cmd=Mover.FRENTE)
            self.connection.send(msg.serialize())

    def tras(self):
        self.motor.move(Mover.TRAS)
        self.current_pos = int(self.current_pos[0]) - 1, int(self.current_pos[1])
        if not self.manual:
            msg = Message(cmd=Mover.TRAS)
            self.connection.send(msg.serialize())

    def esquerda(self):
        self.motor.move(Mover.ESQUERDA)
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) - 1
        if not self.manual:
            msg = Message(cmd=Mover.ESQUERDA)
            self.connection.send(msg.serialize())

    def direita(self):
        self.motor.move(Mover.DIREITA)
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) + 1
        if not self.manual:
            msg = Message(cmd=Mover.DIREITA)
            self.connection.send(msg.serialize())



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


class Automatico:
    def __init__(self, robo):
        super().__init__()
        # self.current_pos = robo.coord_inicial
        self.robo = robo
        self.running = True

    def _calcula_coord(self, flag):
        while not self.robo.current_pos == flag:
            if not flag in global_flags: break
            robot_x, robot_y = int(self.robo.current_pos[0]), int(self.robo.current_pos[1])
            robot_coord = robot_x, robot_y

            # se a bandeira estiver na frente (X) do robo
            # verifica se a prox coord esta ocupada
            # se estiver, passa, caso contrario, anda pra frente
            if robot_x < int(flag[0]):
                if (robot_x + 1, robot_y) in global_map:
                    pass
                else: self.robo.frente()

            if robot_x > int(flag[0]):
                if (robot_x - 1, robot_y) in global_map:
                    pass
                else: self.robo.tras()

            if robot_y < int(flag[1]):
                if (robot_x, robot_y + 1) in global_map:
                    pass
                else: self.robo.direita()

            if robot_x > int(flag[1]):
                if (robot_x, robot_y - 1) in global_map:
                    pass
                else: self.robo.esquerda()

    def run(self):
        for flag in self.robo.flags:
            self._calcula_coord(flag)


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
