import socket
from threading import Thread

import zmq

from Public import *


class ComunicaComSA(Thread):
    """
        Esta classe efetua a comunicacao entre o Sistema Supervisor e o Sistema Auditor

        Divide-se em duas threads
        Thread 1:
            Responsavel por receber e tratar as mensagens broadcast do servidor, ou seja, todas aquelas vidas do socket
            subscribe, sao elas: START, STOP, UPDATE_FLAGS
                * Start = Inicia partida
                * Stop = Termina Partida
                * Update_Flags = Atualiza bandeiras
                * update_map = atualiza lista de posicoes ocupadas
                * MODE = Define o modo de jogo
        Thread 2:
            Responsavel por enviar requisicoes e receber respostas individuais do servidor, ou seja, tudo enviado e
            recebido pelo Socket Dealer.
                * Login: Efetua o Login no Sistema
                * Try_Move: Tenta se mover (o sistema auditor deve autorizar ou nao a movimentacao, verificando se ha
                algum robo naquela posicao)
                * get_flag: Caso o robo encontre uma bandeira, envia uma mensagem ao SA, informando-o da obtencao da mesma.


        Deve-se informar o IP do servidor, a porta e a identificacao do robo. Caso a ID fornecida pelo supervisor nao bata com a
        cadastrada no Sistema Explorador, nao sera possivel conectar.
    """

    def __init__(self, ip, port, id=''):
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
        self.pos = (0, 0)  # posicao

        # em alguns casos eh necessario ter acesso a camada inferior (supervisor)
        self.supervisor = None
        self.name = "comunicacomsa"

    def set_supervisor(self, supervisor):
        self.supervisor = supervisor

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

    def _recv(self):
        while self._thread_run_flag:
            ans = self._sub_socket.recv()
            rep = Message(0, ans)
            self._process_broadcast_messages(rep)

    def _process_broadcast_messages(self, msg):
        print("Comando: ", msg.cmd)
        # Processa Mensagens vinads do socket subscribe
        if msg.cmd == Commands.START:
            # recebe a posicao inicial das cacas
            self.cacas = msg.data
            print("Lista de cacas: ", self.cacas)

            # recebe a posicao inicial
            # pos = self.dealer_socket.recv()
            # pos = Message(0, pos)
            # self.pos = pos.data
            print("Posicao inicial: ", self.pos)
            # self.supervisor.move(self.pos)
            # envia as bandeiras pro sistema do robo
            self.supervisor.send_bandeiras()
            self.supervisor.start_robot()

        elif msg.cmd == Commands.UPDATE_MAP:
            # print("updated map is", msg.data)
            self.supervisor.send_updated_map(msg.data)

        elif msg.cmd == Commands.QUIT:
            # ja que o exit n ta funcionando, vai na forca bruta
            os.kill(os.getpid(), signal.SIGKILL)

        elif msg.cmd == Commands.UPDATE_FLAGS:
            # quando alguem obtem uma caca, o SA manda uma mensagem pra geral atualizando as cacas
            self.cacas = msg.data
            print("Nova lista de cacas eh ", self.cacas)
            # envia as bandeiras pro sistema do robo
            self.supervisor.send_bandeiras()

        elif msg.cmd == Commands.MODE:
            self.supervisor.mode = msg.data
            self.supervisor.set_mode(self.supervisor.mode)
            if self.supervisor.mode:
                print("modo manual")
                if self.supervisor.jogo.is_alive():
                    # se a thread estiver executando, para e reinicia
                    self.supervisor.jogo.join()
                    self.supervisor.start_interface(msg.data)
                else:
                    self.supervisor.start_interface(msg.data)

            else:
                print("modo automatico")
                self.supervisor.jogo.manual = msg.data  # seta como false


        elif msg.cmd == Commands.STOP:
            # self.started = False
            # self.thread_run_flag = False
            self.supervisor.stop()
            print("FIM DA PARTIDA ")
        else:
            pass

    def run(self):
        '''Inicia a Thread, a qual ira tratar todas as mensagens Broadcast do servidor '''
        self._recv()

    def _read_rep(self):
        resp = self.dealer_socket.recv()
        resp = Message(0, resp)
        print("status: ", resp.data[Commands.STATUS], "\ninfo: ", resp.data['info'])
        return resp.data[Commands.STATUS]

    def login(self):
        '''Metodo  para o Login no jogo, envia a ID do robo'''
        dados = {
            Commands.ID: self.id,
            Commands.IP: self.my_ip,
            Commands.INITIAL_POS: self.supervisor.current_pos
        }  # Commands.ID = string 'id', Commands.IP = 'ip', Commands.INITIAL_POS = 'initial_pos'
        req = Message(cmd=Commands.LOGIN, data=dados)
        self.dealer_socket.send(req.serialize())
        self._read_rep()

    def try_move(self, coord):
        """informa ao supervisor que ta indo pra coord"""
        req = Message(cmd=Commands.MOVE_TO, data=coord)
        self.dealer_socket.send(req.serialize())
        # if self._read_rep() == 200:
        #     self.pos = coord
        #     print("Ma current pos is: ", self.pos)
        #     return True
        #
        # print("Ma current pos is: ", self.pos)
        # return False

    def get_flag(self, coord):
        """ Envia mensagem que obteve uma bandeira """
        req = Message(cmd=Commands.GET_FLAG, data=coord)
        self.dealer_socket.send(req.serialize())


if __name__ == "__main__":
    ComunicaComSA("localhost", Commands.PORT_SA)