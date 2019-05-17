import random
import sys
import time
from threading import Thread
import zmq

from SistemaSupervisor import Supervisor
from Public import Message, Commands


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

    def __init__(self, port, SA_ip):
        super().__init__()
        self.port = port
        self.context = zmq.Context()
        self.SA_ip = SA_ip

        self.cacas = []
        self.robo = Robo(self)


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
            if not self.robo.is_alive():
                self.robo.start()  # caso a thread nao tenha sido iniciada, inicia-a
        elif msg.cmd == Commands.STOP:
            self.robo.join(100)
            print("STOP")

        elif msg.cmd == Commands.INITIAL_POS:
            self.robo.current_pos = msg.data
            print("current pos is ", self.robo.current_pos)

        elif msg.cmd == Commands.UPDATE_MAP:
            self.robo.map = msg.data

        elif msg.cmd == Commands.DIRECTION:
            self._process_move(msg.data)

        elif msg.cmd == Commands.MODE:
            if msg.data == False:
                print("MODO AUTOMATICO")
            else: print("MODO MANUAL ")
            self.robo.manual = Commands.MODE
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
        else: pass


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
class Robo:
    """Classe que istancia um robo, basicamente, serve pra se mover e deu"""

    def __init__(self, comunicador):
        super().__init__()
        self.cacas = []
        self.comunicador = comunicador
        self.running = False
        self.daemon = Thread()
        self.map = []
        self.current_pos = None
        self.manual = False

        try: self.mover = Mover(0,0)
        except Exception as e:
            pass


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

    def frente(self):
        # anda pra frente e incrementa 1 em X
        x,y = self.current_pos[0] + 1, self.current_pos[1]
        try:
            self.mover.move(Mover.FRENTE)
        except Exception as e: pass
        return x,y

    def tras(self):
        # anda pra tras e decrementa 1 em X
        x, y = self.current_pos[0] - 1, self.current_pos[1]
        try:
            self.mover.move(Mover.TRAS)
        except Exception as e:
            pass
        return x, y

    def direita(self):
        # anda pra direita e incrementa 1 em Y
        x, y = self.current_pos[0], self.current_pos[1] + 1
        try:
            self.mover.move(Mover.DIREITA)
        except Exception as e:
            pass
        return x, y

    def esquerda(self):
        # anda pra esquerda e decrementa 1 em Y
        x, y = self.current_pos[0], self.current_pos[1] - 1
        try:
            self.mover.move(Mover.ESQUERDA)
        except Exception as e:
            pass
        return x, y


    def move(self, coord):
        if not coord in self.map:
            print("Robo andando para: ", coord)
            time.sleep(random.randint(1,10))
            print("chegou")
        else: print("posicao ja ocupada")


    def start(self):
        self.daemon = Thread(target=self._run)
        self.daemon.daemon = True
        self.daemon.start()

    def is_alive(self):
        return self.daemon.is_alive()

    def join(self, timeout):
        self.running = False
        self.daemon.join(timeout=timeout)

    def _run(self):
        if not self.running: self.running = True
        if not self.manual: self._get_bandeiras()




########################################################################################################################

if __name__ == "__main__":

    if len(sys.argv) == 4:
        print("flag is", sys.argv[1])
        ip = sys.argv[2]
        name = sys.argv[3]
        c = Comunicador(Commands.PORT_SA, ip)
        c.connect_to_supervisor(ip)
        c.start()
    else:
        ip = sys.argv[1]
        name = sys.argv[2]
        c = Comunicador(Commands.PORT_SA, ip)
        c.connect(name)
        c.start()
