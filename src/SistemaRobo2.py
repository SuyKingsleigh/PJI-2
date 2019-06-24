from threading import Thread

import zmq

from SistemaSupervisor import Supervisor

from Public import Message, Commands


class Dispatcher(Thread):
    def __init__(self, port, sa_ip, ip_robo):
        super().__init__()
        self.port = port
        self.SA_ip = sa_ip
        self.robo_ip = ip_robo

        self.context = zmq.Context()
        self.map = []
        self.current_pos = -1,-1
        self.manual = False

    def _connect_to_supervisor(self, ip):
        # conecta ao respectivo S.S
        self._dealer_socket = self.context.socket(zmq.DEALER)
        self._dealer_socket.connect("tcp://%s:%d" % (ip, Supervisor.SUPERVISOR_PORT))

        # envia uma mensagem pro ss (so pra testar msm)
        msg = Message(cmd=Commands.CONNECT_TO_SS)
        self._dealer_socket.send(msg.serialize())


    def _recv(self):
        while True:
            recv = self.dealer_socket.recv()
            recv = Message(0, recv)
            self._process_cmd(recv)

    def _process_cmd(self, msg):
        pass