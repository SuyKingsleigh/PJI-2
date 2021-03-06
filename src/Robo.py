import socket
import sys
import time
from threading import Thread

from Public import Message, Commands, Mover
from Move import Robo as robot

global debug
global orientation

version = "Red Hot"

class Robo(Thread):
    """essa classe eh para ser executada no robo, a unica coisa que essa classe faz
    eh mover o robo, e eventualmente ativar o modo automatico"""

    FRONT = "w"
    BACK = "s"
    RIGHT = "d"
    LEFT = "a"

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
        global orientation
        self._last_dir = orientation
        self._begin_orientation = orientation

        print("orientation is: ", self._last_dir)
        global debug
        if not debug:
            try:
                self.motor = robot()
                print("motor connected")
            except Exception as e:
                print("failled to connect motor", e)

    def _process_data(self, msg):
        # print(msg)
        if msg.cmd == Mover.FRENTE:
            print("frente")
            try:
                self.frente()
            except Exception as e:
                pass

        elif msg.cmd == Mover.TRAS:
            print("tras")
            try:
                self.tras()
            except Exception as e:
                pass

        elif msg.cmd == Mover.DIREITA:
            print("direita")
            try:
                self.direita()
            except Exception as e:
                pass

        elif msg.cmd == Mover.ESQUERDA:
            print("esquerda")
            try:
                self.esquerda()
            except Exception as e:
                pass

        elif msg.cmd == Commands.STOP:
            self.current_pos = self.begin_pos
            self._last_dir = self._begin_orientation
            self.flags = None
            if self.auto_thread:
                if self.auto_thread.is_alive():
                    self.auto_thread.join(timeout=10)
                    self.auto_thread = None

            if not debug:
                try:
                    self.motor = robot()
                    print("motor connected")
                except Exception as e:
                    print("[NOVO MANUAL] failled to connect motor: ", e)

            print("STOP")

        elif msg == Commands.QUIT:
            try:
                self.join()
                self.socket.close()
            except:
                pass

        elif not msg:
            time.sleep(1)

        elif msg.cmd == Commands.UPDATE_MAP:
            print("mapa: ", msg.data)
            self.map = msg.data

        elif msg.cmd == Commands.UPDATE_FLAGS:
            print("bandeiras: ", msg.data)
            self.flags = msg.data

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
                    if self.auto_thread.is_alive():
                        self.auto_thread.join(timeout=10)
                        self.auto_thread = None

        elif msg.cmd == Commands.STATUS_GET_FLAG:
            self._blocked = False

    def frente(self):
        self._mover(dir=Robo.FRONT)
        self.current_pos = int(self.current_pos[0]) + 1, int(self.current_pos[1])
        print(self.current_pos)
        if not self.manual:
            msg = Message(cmd=Mover.FRENTE)
            self.connection.send(msg.serialize())
            time.sleep(Automatico.SLEEP_TIME)

    def tras(self):
        self._mover(dir=Robo.BACK)
        self.current_pos = int(self.current_pos[0]) - 1, int(self.current_pos[1])
        print(self.current_pos)
        if not self.manual:
            msg = Message(cmd=Mover.TRAS)
            self.connection.send(msg.serialize())
            time.sleep(Automatico.SLEEP_TIME)

    def esquerda(self):
        self._mover(dir=Robo.LEFT)
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) - 1
        print(self.current_pos)
        if not self.manual:
            msg = Message(cmd=Mover.ESQUERDA)
            self.connection.send(msg.serialize())
            time.sleep(Automatico.SLEEP_TIME)

    def direita(self):
        self._mover(dir=Robo.RIGHT)
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) + 1
        print(self.current_pos)
        if not self.manual:
            msg = Message(cmd=Mover.DIREITA)
            self.connection.send(msg.serialize())
            time.sleep(Automatico.SLEEP_TIME)

    def _mover(self, dir):
        if debug:
            self._last_dir = dir
            return

        if self._last_dir == Robo.FRONT:
            if dir == Robo.FRONT:
                self.motor.frente()
            elif dir == Robo.RIGHT:
                self.motor.direita()
            elif dir == Robo.LEFT:
                self.motor.esquerda()
            elif dir == Robo.BACK:
                self.motor.tras()

        elif self._last_dir == Robo.RIGHT:
            if dir == Robo.FRONT:
                self.motor.esquerda()
            elif dir == Robo.LEFT:
                self.motor.tras()
            elif dir == Robo.RIGHT:
                self.motor.frente()
            elif dir == Robo.BACK:
                self.motor.direita()

        elif self._last_dir == Robo.LEFT:
            if dir == Robo.FRONT:
                self.motor.direita()
            elif dir == Robo.LEFT:
                self.motor.frente()
            elif dir == Robo.RIGHT:
                self.motor.tras()
            elif dir == Robo.BACK:
                self.motor.esquerda()

        elif self._last_dir == Robo.BACK:
            if dir == Robo.FRONT:
                self.motor.tras()
            elif dir == Robo.LEFT:
                self.motor.direita()
            elif dir == Robo.RIGHT:
                self.motor.esquerda()
            elif dir == Robo.BACK:
                self.motor.frente()

        self._last_dir = dir

    def _connect(self):
        """Conecta o robo ao controlador"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)
        print("ready to conect")
        self.connection, self.address = self.socket.accept()

        print("conectado com, ", self.address)

    def _send_begin_pos(self):
        self.connection.send(Message(cmd=Commands.SET_BEGIN_POS, data=self.begin_pos).serialize())

    def _handle(self):
        while True:
            try:
                msg = self.connection.recv(2048)
                print(msg, file=sys.stderr)
                msg = Message(None, msg)
                self._process_data(msg)
            except Exception as e:
                print(e.with_traceback)

    def run(self):
        self._connect()
        self._handle()

    def is_blocked(self):
        return self._blocked

    def get_flag(self, coord):
        self.connection.send(Message(cmd=Commands.GET_FLAG, data=coord).serialize())
        self._blocked = True

    def close_socket(self):
        try:
            self.connection.close()
        except Exception as e:
            print(e)
        finally:
            self.socket.close()
            print("main socket has been closed")


#########################################################################################################################################

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
            # 1])
            robot_x, robot_y = self.robo.current_pos[0], self.robo.current_pos[1]
            old_coord = robot_x, robot_y
            # se a bandeira estiver na frente (X) do robo
            # verifica se a prox coord esta ocupada
            # se estiver, passa, caso contrario, anda pra frente
            if robot_x < flag[0] and self.robo.current_pos != flag:
                if (robot_x + 1, robot_y) not in self.robo.map:
                    print("indo para frente, yeehaaaw")
                    self.robo.frente()
                else:
                    time.sleep(Automatico.SLEEP_TIME)

            elif robot_x > flag[0] and self.robo.current_pos != flag:
                if (robot_x - 1, robot_y) not in self.robo.map:
                    print("indo para tras, Pi, Pi, Pi, 3.14, Pi")
                    self.robo.tras()
                else:
                    time.sleep(Automatico.SLEEP_TIME)

            elif robot_y < flag[1] and self.robo.current_pos != flag:
                if (robot_x, robot_y + 1) not in self.robo.map:
                    self.robo.direita()

                    print("direita\n")
                else:
                    time.sleep(Automatico.SLEEP_TIME)

            elif robot_x > flag[1] and self.robo.current_pos != flag:
                if (robot_x, robot_y - 1) not in self.robo.map:
                    print("esquerda\n")
                    self.robo.esquerda()
                else:
                    time.sleep(Automatico.SLEEP_TIME)

            if old_coord == self.robo.current_pos: break  # previnir entrar nuns loop doidao
            if not self.robo.flags: break
            print("posicao atual do robo eh: ", self.robo.current_pos)

        print("achou a bandeira")
        if (self.robo.current_pos == flag): self.robo.get_flag(self.robo.current_pos)

    def run(self):
        while not self.robo.flags: pass
        self.robo.flags.sort()
        for flag in self.robo.flags:
            print("indo atras da bandeira", flag)
            self._calcula_coord(flag)


if __name__ == "__main__":
    """PARAMETROS PARA TESTE EM LOCALHOST 
    localhost 0 0"""
    port = 42069
    print("Version: ", version)
    global debug
    global orientation
    debug = False
    orientation = Robo.FRONT

    i = 0
    for arg in sys.argv:
        if arg == "debug": debug = True
        if arg == "-o" or arg == "-O":
            orientation = sys.argv[i + 1]
        i += 1

    if debug: print("debug mode")
    coord = int(sys.argv[1]), int(sys.argv[2])
    try:
        robo = Robo("0.0.0.0", port, coord)
        robo.run()
    except KeyboardInterrupt:
        robo.close_socket()