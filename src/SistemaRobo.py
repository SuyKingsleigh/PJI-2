import random
import socket
import sys
from threading import Thread

import zmq
from Public import Message, Commands
from SistemaSupervisor import Supervisor
from mover import Mover

HOST = 'localhost'


class Comunicador(Thread):
    """ Classe responsavel pela comunicacao com o SS
        Inicialmente envia uma mensagem para o SA, apenas perguntando o IP do SS
        Descobre o IP a partir do NOME do SS.
        EH DE SUMA IMPORTANCIA QUE O NOME CADASTRADO NO SS E NO SR SEJAM OS MESMOS
        CASO CONTRARIO NAO SERA POSSIVEL ESTABELECER UMA COMUNICCACAO
    """
    SLEEP_TIME = 3

    def __init__(self, port, SA_ip, ip_robo):
        super().__init__()
        self.port = port
        self.context = zmq.Context()

        self.SA_ip = SA_ip

        self.cacas = []
        self.robo = Controlador(self, ip_robo)

    def connect(self, player_id):
        # cria um socket temporario, envia a solicitacao pro servidor
        socket = self.context.socket(zmq.DEALER)
        socket.connect("tcp://%s:%d" % (self.SA_ip, self.port + 1))
        msg = Message(cmd=Commands.GET_IP, data=player_id)
        socket.send(msg.serialize())

        # recebe a resposta do servidor
        rep = socket.recv()
        rep = Message(0, rep)
        # self.SS_ip = rep.data
        self.connect_to_supervisor(rep.data)
        print(rep.data)

    def connect_to_supervisor(self, ip):
        # conecta ao respectivo S.S
        self.dealer_socket = self.context.socket(zmq.DEALER)
        self.dealer_socket.connect("tcp://%s:%d" % (ip, Supervisor.SUPERVISOR_PORT))

        # envia uma mensagem pro ss (so pra testar msm)
        msg = Message(cmd=Commands.CONNECT_TO_SS)
        self.dealer_socket.send(msg.serialize())

    def _recv(self):
        while True:
            recv = self.dealer_socket.recv()
            recv = Message(0, recv)
            self._process_cmd(recv)

    def _process_cmd(self, msg):
        print("recebeu a mensagem: ", msg.cmd)
        if msg.cmd == Commands.MOVE_TO:
            if msg.get("status") == 200:
                print("movimento autorizado")
                self.robo.move(msg.get("data"))
        elif msg.cmd == Commands.STATUS:
            print(" status: ", msg.data)

        elif msg.cmd == Commands.START:
            self.robo.running = True

        elif msg.cmd == Commands.UPDATE_FLAGS:
            print("bandeiras a pegar", msg.data)
            self.robo.set_bandeiras(msg.data)
            self.robo.send_flags(msg.data)
            if not self.robo.is_alive():
                self.robo.start()  # caso a thread nao tenha sido iniciada, inicia-a
        elif msg.cmd == Commands.STOP:
            # self.robo.join(100)
            print("STOP")

        elif msg.cmd == Commands.INITIAL_POS:

            x, y = int(msg.data[0]), int(msg.data[1])
            self.robo.current_pos = [x, y]
            print("current pos is ", self.robo.current_pos)

        elif msg.cmd == Commands.UPDATE_MAP:
            self.robo.map = msg.data

        elif msg.cmd == Commands.DIRECTION:
            self._process_move(msg.data)

        elif msg.cmd == Commands.MODE:
            if msg.data:
                print("MODO MANUAL ")
            else:
                print("MODO AUTOMATICO")
            # self.robo.manual = Commands.MODE
            self.robo.set_mode(msg.data)

        elif msg.cmd == Commands.STATUS_GET_FLAG:
            self.robo.unblock_robot()
        else:
            pass

    def run(self):
        self._recv()

    def _process_move(self, data):
        if data == Mover.FRENTE:
            self.robo.frente()
            print("indo pra frente")
        elif data == Mover.TRAS:
            self.robo.tras()
            print("indo para tras")
        elif data == Mover.DIREITA:
            self.robo.direita()
            print("indo para direita")
        elif data == Mover.ESQUERDA:
            self.robo.esquerda()
            print("indo para a esquerda")
        else:
            pass

    def get_flag(self, msg):
        print("Comunicador esta a enviar um getflag ", "cmd=", msg.cmd, " data=", msg.data)
        self.dealer_socket.send(msg.serialize())

    def try_move(self, coord):
        """tenta se mover
         envia a coord para qual vai ir
         se autorizado recebe 200
         se nao 400.
         """
        req = Message(cmd=Commands.MOVE_TO, data=coord)
        self.dealer_socket.send(req.serialize())
        if coord in self.robo.cacas:
            msg = Message(cmd=Commands.GET_FLAG, data=coord)
            self.dealer_socket.send(msg.serialize())

        self.robo.current_pos = coord
        self.robo.move(coord)


########################################################################################################################
class Controlador:
    """Classe que istancia um robo, basicamente, serve pra se mover e deu"""

    def __init__(self, comunicador, ip_robo):
        super().__init__()
        self.cacas = []
        self.comunicador = comunicador
        self.running = False
        self.daemon = Thread()
        self.map = []
        self.current_pos = -1, -1
        self.manual = False

        self.ip_robo = ip_robo
        self._socket = socket.socket()  # socket.AF_INET, socket.SOCK_STREAM
        self._socket.connect((self.ip_robo, 42069))

    def close(self):
        self._socket.close()

    def _get_bandeiras(self):
        for bandeira in self.cacas:
            if self.running:
                print(bandeira)
                self.comunicador.try_move(bandeira)
            else:
                break

        if not self.cacas:
            self.running = False
            print("Nao ha mais bandeiras")

    def set_bandeiras(self, bandeiras):
        self.cacas = bandeiras

    def send_flags(self, bandeiras):
        self._socket.send(Message(cmd=Commands.UPDATE_FLAGS, data=bandeiras).serialize())

    def send_map(self, map):
        self._socket.send(Message(cmd=Commands.UPDATE_MAP, data=map).serialize())

    def frente(self):
        # anda pra frente e incrementa 1 em X
        self.current_pos = int(self.current_pos[0]) + 1, int(self.current_pos[1])
        try:  # envia uma mensagem para o robo para se mover
            self._socket.send(Message(cmd=Mover.FRENTE).serialize())
        except Exception as e:
            print("falhou ao mover", e)

        # fica bloqeuado ate receber a resposta do robo
        if not self.manual:
            while not self._socket.recv(256): pass
        print("posicao atual eh: ", self.current_pos)

        return self.current_pos[0], self.current_pos[1]

    def tras(self):
        # anda pra tras e decrementa 1 em X
        self.current_pos = int(self.current_pos[0]) - 1, int(self.current_pos[1])
        try:
            self._socket.send(Message(cmd=Mover.TRAS).serialize())
        except Exception as e:
            pass
        if not self.manual:
            while not self._socket.recv(256): pass
        print("posicao atual eh: ", self.current_pos)
        return self.current_pos[0], self.current_pos[1]

    def direita(self):
        # anda pra direita e incrementa 1 em Y
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) + 1
        try:
            self._socket.send(Message(cmd=Mover.DIREITA).serialize())
        except Exception as e:
            pass
        if not self.manual:
            while not self._socket.recv(256): pass

        print("posicao atual eh: ", self.current_pos)
        return self.current_pos[0], self.current_pos[1]

    def esquerda(self):
        # anda pra esquerda e decrementa 1 em Y
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) - 1
        try:

            self._socket.send(Message(cmd=Mover.ESQUERDA).serialize())
        except Exception as e:
            pass
        if not self.manual:
            while not self._socket.recv(256): pass
        print("posicao atual eh: ", self.current_pos)
        return self.current_pos[0], self.current_pos[1]

    def move(self, coord):
        if not coord in self.map:
            print("Robo andando para: ", coord)
            time.sleep(random.randint(1, 10))
            print("chegou")
        else:
            print("posicao ja ocupada")

    def start(self):
        self.daemon = Thread(target=self._run)
        self.listend = Thread(target=self._listen)
        self.listend.daemon = True
        self.daemon.daemon = True
        self.daemon.start()
        self.listend.start()

    def send_stop(self):
        self._socket.send(Message(cmd=Commands.STOP).serialize())

    def is_alive(self):
        return self.daemon.is_alive()

    def unblock_robot(self):
        self._socket.send(Message(cmd=Commands.STATUS_GET_FLAG).serialize())

    def join(self, timeout):
        self.running = False
        self.daemon.join(timeout=timeout)

    def set_mode(self, mode):
        self.manual = mode
        self._socket.send(Message(cmd=Commands.MODE, data=mode).serialize())

    def _handle(self, msg):
        if msg.cmd == Mover.DIREITA:
            x, y = int(self.current_pos[0]), int(self.current_pos[1]) + 1
            self.comunicador.try_move((x, y))

        elif msg.cmd == Mover.ESQUERDA:
            x, y = int(self.current_pos[0]), int(self.current_pos[1]) - 1
            self.comunicador.try_move((x, y))

        elif msg.cmd == Mover.FRENTE:
            x, y = int(self.current_pos[0]) + 1, int(self.current_pos[1])
            self.comunicador.try_move((x, y))

        elif msg.cmd == Mover.TRAS:
            x, y = int(self.current_pos[0]) - 1, int(self.current_pos[1])
            self.comunicador.try_move((x, y))

        elif msg.cmd == Commands.GET_FLAG:
            self.comunicador.get_flag(msg)
            print("Controlador recebeu um get flag ", msg.data, "\n")

        else:
            time.sleep(0.3)

        print("\ncurrent pos is:  ", self.current_pos)

    def _listen(self):
        while True:
            try:
                msg = self._socket.recv(2048)
                msg = Message(None, msg)
                self._handle(msg)
            except Exception as e:
                pass

    def _run(self):
        if not self.running: self.running = True


########################################################################################################################

if __name__ == "__main__":
    """PARAMETROS PARA TESTE EM LOCALHOST
    localhost jamal localhost"""
    if len(sys.argv) == 5:
        print("flag is", sys.argv[1])  # flag '-S'
        ip = sys.argv[2]  # ip do supervisor
        name = sys.argv[3]  # nome do robo
        ip_robo = sys.argv[4]  # ip do robo

        c = Comunicador(Commands.PORT_SA, ip, ip_robo)
        c.connect_to_supervisor(ip)
        c.start()
    else:
        ip = sys.argv[1]  # ip do auditor
        name = sys.argv[2]  # nome do robo
        ip_robo = sys.argv[3]  # ip do robo

        c = Comunicador(Commands.PORT_SA, ip, ip_robo)
        c.connect(name)
        c.start()
