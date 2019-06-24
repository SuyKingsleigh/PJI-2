import socket
import sys
import time
from threading import Thread

from Public import Message, Commands
from manual import Manual
from mover import Mover


class Robo(Thread):
    """essa classe eh para ser executada no robo, a unica coisa que essa classe faz
    eh mover o robo, e eventualmente ativar o modo automatico"""

    def __init__(self, ip, port, coord_inicial):
        super().__init__()
        # self.socket = socket.socket()
        self.port = port
        self.ip = ip
        self.begin_pos = coord_inicial
        self.current_pos = coord_inicial
        self.manual = True

        self.map = []
        self.flags = []
        self._blocked = False
        self.auto_thread = None
        # global flags
        try:
            self.motor = Manual((self.current_pos[0], self.current_pos[1]))
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

        elif msg == Commands.STOP:
            self.current_pos = self.begin_pos
            self.flags = []

        elif msg == Commands.QUIT:
            self.join()
            self.socket.close()

        elif not msg:
            time.sleep(1)

        elif msg.cmd == Commands.UPDATE_MAP:
            print("mapa: ", msg.data)
            self.map = msg.data
            # global global_map
            # global_map = self.map


        elif msg.cmd == Commands.UPDATE_FLAGS:
            print("bandeiras: ", msg.data)
            self.flags = msg.data
            # global global_flags
            # global_flags = self.flags

        elif msg.cmd == Commands.MODE:
            # automatico = False
            self.manual = msg.data
            print(msg.data)
            if not msg.data:
                print("Modo automatico\n")
                self.auto_thread = Automatico(self)
                self.auto_thread.start()
            else:
                print("Modo manual\n")
                if self.auto_thread:
                    if self.auto_thread.is_alive(): self.auto_thread.join(timeout=10)

        elif msg.cmd == Commands.STATUS_GET_FLAG:
            self._blocked = False

        else:
            pass
            # time.sleep(0.5)

    def frente(self):
        try:
            self.motor.move(Mover.FRENTE)
        except Exception as e:
            pass
        self.current_pos = int(self.current_pos[0]) + 1, int(self.current_pos[1])
        print(self.current_pos)
        if not self.manual:
            msg = Message(cmd=Mover.FRENTE)
            self.connection.send(msg.serialize())
            return True
        return 

    def tras(self):
        try:
            self.motor.move(Mover.TRAS)
        except Exception as e:
            pass
        self.current_pos = int(self.current_pos[0]) - 1, int(self.current_pos[1])
        print(self.current_pos)
        if not self.manual:
            msg = Message(cmd=Mover.TRAS)
            self.connection.send(msg.serialize())
            return True
        return 

    def esquerda(self):
        try:
            self.motor.move(Mover.ESQUERDA)
        except Exception as e:
            pass
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) - 1
        print(self.current_pos)
        if not self.manual:
            msg = Message(cmd=Mover.ESQUERDA)
            self.connection.send(msg.serialize())
            return True
        return

    def direita(self):
        try:
            self.motor.move(Mover.DIREITA)
        except Exception as e:
            pass
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) + 1
        print(self.current_pos)
        if not self.manual:
            msg = Message(cmd=Mover.DIREITA)
            self.connection.send(msg.serialize())
            return True 
        return 

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

    def is_blocked(self):
        return self._blocked

    def get_flag(self, coord):
        self.connection.send(Message(cmd=Commands.GET_FLAG, data=coord).serialize())
        self._blocked = True


class Automatico(Thread):
    SLEEP_TIME = 1.5
    def __init__(self, robo):
        super().__init__()
        self.current_pos = robo.begin_pos
        self.robo = robo
        self.running = True

    def _calcula_coord(self, flag):
        flag = tuple(flag)
        print("flag=", flag)
        print("current_pos=", self.robo.current_pos)

        # enquanto estiver bloequado fica nessa porra de loop
        while self.robo.is_blocked(): pass

        # quando desbloqueia vem pra esse
        while not self.robo.current_pos == flag:
            # robot_x, robot_y = int(self.robo.current_pos[0]), int(self.robo.current_pos[
            #1])
            robot_x, robot_y = self.robo.current_pos[0], self.robo.current_pos[1]
            old_coord = robot_x, robot_y
            # se a bandeira estiver na frente (X) do robo
            # verifica se a prox coord esta ocupada
            # se estiver, passa, caso contrario, anda pra frente
            if robot_x < flag[0] and self.robo.current_pos != flag:
                if (robot_x + 1, robot_y) not in self.robo.map:
                    print("indo para frente, yeehaaaw")
                    self.robo.frente()
                    time.sleep(Automatico.SLEEP_TIME)

            elif robot_x > flag[0] and self.robo.current_pos != flag:
                if (robot_x - 1, robot_y) not in self.robo.map:
                    print("indo para tras, Pi, Pi, Pi, 3.14, Pi")
                    self.robo.tras()
                    time.sleep(Automatico.SLEEP_TIME)

            elif robot_y < flag[1] and self.robo.current_pos != flag:
                if (robot_x, robot_y + 1) not in self.robo.map:
                    self.robo.direita()
                    time.sleep(Automatico.SLEEP_TIME)

                    print("direita\n")

            elif robot_x > flag[1] and self.robo.current_pos != flag:
                if (robot_x, robot_y - 1) not in self.robo.map:
                    print("esquerda\n")
                    self.robo.esquerda()
                    time.sleep(Automatico.SLEEP_TIME)

            if old_coord == self.robo.current_pos: break # previnir entrar nuns loop doidao
            print("posicao atual do robo eh: ", self.robo.current_pos)


        print("achou a bandeira")
        if(self.robo.current_pos == flag): self.robo.get_flag(self.robo.current_pos)

    def run(self):
        while not self.robo.flags: pass
        for flag in self.robo.flags:
            print("indo atras da bandeira", flag)
            self._calcula_coord(flag)


if __name__ == "__main__":
    print("versao 24.14.43")
    """PARAMETROS PARA TESTE EM LOCALHOST 
    localhost 0 0"""
    port = 42069
    coord = int(sys.argv[1]), int(sys.argv[2])
    Robo("0.0.0.0", port, coord).run()