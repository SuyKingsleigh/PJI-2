import sys
import time
from threading import Thread

import zmq

from SistemaSupervisor import Supervisor
from Public import Message, Commands

HOST = 'localhost'

class Comunicador(Thread):
    """Classe responsavel pela comunicacao com o SS
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

        self.run_flag = True
        self.cacas = []
        self.posicao_ocupadas = []

    def connect(self, player_id):
        # cria um socket temporario, envia a solicitacao pro servidor
        socket = self.context.socket(zmq.DEALER)
        socket.connect("tcp://%s:%d" % (self.SA_ip, self.port + 1))
        msg = Message(cmd=Commands.GET_IP, data=player_id)
        socket.send(msg.serialize())

        # recebe a resposta do servidor
        rep = socket.recv()
        rep = Message(0, rep)
        self.SS_ip = rep.data
        print(rep.data)

        # conecta ao respectivo S.S
        self.dealer_socket = self.context.socket(zmq.DEALER)
        self.dealer_socket.connect("tcp://%s:%d" % (self.SS_ip, Supervisor.SUPERVISOR_PORT))

        # envia uma mensagem pro ss (so pra testar msm)
        msg = Message(cmd=Commands.CONNECT_TO_SS)
        self.dealer_socket.send(msg.serialize())


    def _recv(self):
        while True:
            recv = self.dealer_socket.recv()
            recv = Message(0, recv)
            self._process_cmd(recv)


    def _process_cmd(self,msg):
        if msg.cmd == Commands.MOVE_TO:
            # print(msg.data)
            if msg.get("status") == 200:
                print("movimento autorizado")
                self._move(msg.get("data"))
        elif msg.cmd == Commands.STATUS:
            print(msg.data)

        elif msg.cmd == Commands.UPDATE_FLAGS:
            print("bandeiras a pegar", msg.data)
            self.cacas = msg.data
        elif msg.cmd == Commands.UPDATE_MAP:
            print("\nPosicoes ocupadas", msg.data)
            self.posicao_ocupadas = msg.data

        else:
            pass

    def run(self):
        self._recv()


    def _try_move(self, coord):
        """tenta se mover
         envia a coord para qual vai ir
         se autorizado recebe 200
         se nao 400.
         """
        req = Message(cmd=Commands.MOVE_TO, data=coord)
        self.dealer_socket.send(req.serialize())
        if coord in self.cacas:
            msg = Message(cmd=Commands.GET_FLAG, data=coord)
            self.dealer_socket.send(msg.serialize())

        self._move(coord)

    def _move(self, coord):
        print("Andando para: ", coord)
        time.sleep(Comunicador.SLEEP_TIME)
        print("chegou")


    def _get_bandeiras(self):
        """METODO EXCLUSIVO PARA TESTES E TALZ"""
        for bandeira in self.cacas:
            print(bandeira)
            self._try_move(bandeira)

########################################################################################################################
class Robo:
    """Classe que istancia um robo, basicamente, serve pra se mover e deu"""
    pass

########################################################################################################################
class Explorador:
    """Responsavel pela inteligencia do sistema explorador"""
    def calcula_coord(self):
        pass

########################################################################################################################

if __name__ == "__main__":
    # ip = sys.argv[1]
    # name = sys.argv[2]

    ip, name = "localhost", "jamal" # para testes somente

    c = Comunicador(Commands.PORT_SA, ip)
    c.connect(name)
    c.start()

    while(not c.cacas): pass
    c._get_bandeiras()
