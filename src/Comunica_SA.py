import socket
from threading import Thread
from Public import *
import zmq

# from src.Public import Commands


class Comunica_SA(Thread):
    def __init__(self, port, ip):
        super().__init__()
        self.daemon = True

        self.port = port
        self.servers_ip = ip
        self.my_ip = self._get_my_ip()
        self.id = id
        self._thread_run_flag = True  # flag que permite a execucao da thread

        # criacao dos sockets, dealer_socket manda mensagens para o servidor
        # sub_socket recebe mensagens do servidor (mensagens as quais sao enviadas para todos os clientes)
        self.context = zmq.Context()
        self.dealer_socket = self.context.socket(zmq.DEALER)
        self._sub_socket = self.context.socket(zmq.SUB)

        # inscreve para todos os topicos
        self._sub_socket.setsockopt(zmq.SUBSCRIBE, b"")
        self._sub_socket.setsockopt(zmq.LINGER, 0)

        # conecta os sockets
        self._sub_socket.connect("tcp://%s:%d" % (self.servers_ip, port))
        self.dealer_socket.connect("tcp://%s:%d" % (self.servers_ip, self.port + 1))

        # dados da partida
        self.cacas = []
        self.started = False  # flag para indicar se o jogo comecou ou nao



    def _get_my_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.my_ip = s.getsockname()[0]
        print("IP do Supervisor", self.my_ip)
        try:
            s.close()
        except Exception as e:
            pass
        return self.my_ip

    def login(self, id, posicao):
        '''Metodo  para o Login no jogo, envia a ID do robo
            id = nome do robo, STRING
            posicao = posicao do robo, (coordX, coordY)
        '''
        dados = {
            Commands.ID: id,
            Commands.IP: self.my_ip,
            Commands.INITIAL_POS: posicao
        }
        req = Message(cmd=Commands.LOGIN, data=dados)
        self.dealer_socket.send(req.serialize())
        self._read_rep()

    def try_move(self, coord):
        """
        informa ao supervisor que ta indo pra coord
        coord = (coordX, coordY)
        """
        req = Message(cmd=Commands.MOVE_TO, data=coord)
        self.dealer_socket.send(req.serialize())

    def get_flag(self, coord):
        """
        Envia mensagem que obteve uma bandeira
        coord = (coordX, coordY) tupla de inteiros"""
        req = Message(cmd=Commands.GET_FLAG, data=coord)
        self.dealer_socket.send(req.serialize())

