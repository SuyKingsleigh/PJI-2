import socket, sys

import zmq
from threading import Thread
from Public import Message, Commands


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
        self.port = port
        self.servers_ip = ip
        self.my_ip = self._get_my_ip()
        self.id = id
        self.thread_run_flag = True  # flag que permite a execucao da thread

        # criacao dos sockets, dealer_socket manda mensagens para o servidor
        # sub_socket recebe mensagens do servidor (mensagens as quais sao enviadas para todos os clientes)
        self.context = zmq.Context()
        self.dealer_socket = self.context.socket(zmq.DEALER)
        self.sub_socket = self.context.socket(zmq.SUB)

        # inscreve para todos os topicos
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, b"")
        self.sub_socket.setsockopt(zmq.LINGER, 0)

        # conecta os sockets
        self.sub_socket.connect("tcp://%s:%d" % (self.servers_ip, port))
        self.dealer_socket.connect("tcp://%s:%d" % (self.servers_ip, self.port + 1))

        # dados da partida
        self.cacas = []
        self.started = False  # flag para indicar se o jogo comecou ou nao
        self.pos = (0, 0)

        # em alguns casos eh necessario ter acesso a camada inferior (supervisor)
        self.supervisor = None

    def set_supervisor(self, supervisor):
        self.supervisor = supervisor

    def _get_my_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.my_ip = s.getsockname()[0]
        try:
            s.close()
        except Exception as e:
            pass
        return self.my_ip

    def _recv(self):
        while self.thread_run_flag:
            ans = self.sub_socket.recv()
            rep = Message(0, ans)
            self._process_broadcast_messages(rep)

    def _process_broadcast_messages(self, msg):
        # Processa Mensagens vinads do socket subscribe
        if msg.cmd == Commands.START:
            # recebe a posicao inicial das cacas
            self.cacas = msg.data
            print("Lista de cacas: ", self.cacas)

            # recebe a posicao inicial
            pos = self.dealer_socket.recv()
            pos = Message(0, pos)
            self.pos = pos.data
            print("Posicao inicial: ", self.pos)
            self.started = True
            self.supervisor.move(self.pos)
            # envia as bandeiras pro sistema do robo
            self.supervisor.send_bandeiras()

        elif msg.cmd == Commands.UPDATE_FLAGS:
            # quando alguem obtem uma caca, o SA manda uma mensagem pra geral atualizando as cacas
            self.cacas = msg.data
            print("Nova lista de cacas eh ", self.cacas)
            # envia as bandeiras pro sistema do robo
            self.supervisor.send_bandeiras()

        elif msg.cmd == Commands.STOP:
            self.started = False
            self.thread_run_flag = False
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
            'id': self.id,
            'ip': self.my_ip
        }
        req = Message(cmd=Commands.LOGIN, data=dados)
        self.dealer_socket.send(req.serialize())
        self._read_rep()

    def try_move(self, coord):
        """Tenta se mover"""
        req = Message(cmd=Commands.MOVE_TO, data=coord)
        self.dealer_socket.send(req.serialize())
        if self._read_rep() == 200:
            self.pos = coord
            print("Ma current pos is: ", self.pos)
            return True

        print("Ma current pos is: ", self.pos)
        return False

    def get_flag(self, coord):
        """ Envia mensagem que obteve uma bandeira """
        req = Message(cmd=Commands.GET_FLAG, data=coord)
        self.dealer_socket.send(req.serialize())


########################################################################################################################

class Supervisor(Thread):
    SUPERVISOR_PORT = 9999  # porta

    """Interface que faz a comunicacao entre o SR e o proprio sistema, camada mais abaixo do SS"""

    def __init__(self, comunica_com_sa):
        super().__init__()

        # cria interface para comunicacao com o sistema AUDITOR
        self.comunica_com_sa = comunica_com_sa

        # socket para comunicar com o SISTEMA EXPLORADOR
        self.context = zmq.Context()
        self.router_socket = self.context.socket(zmq.ROUTER)
        self.router_socket.bind("tcp://*:%s" % str(Supervisor.SUPERVISOR_PORT))

        # poller
        self.poller = zmq.Poller()
        self.poller.register(self.router_socket, zmq.POLLIN)  # notifica cada mensagem recebida

        self.run_flag = True

    def _process_cmd(self, msg):
        address = msg.address
        # recebe mensagem de obtem bandeira
        if msg.cmd == Commands.GET_FLAG:
            self.comunica_com_sa.get_flag(msg.data)

        # robo informa ao supervisor que quer ir para X,Y posicao
        elif msg.cmd == Commands.MOVE_TO:
            if self.comunica_com_sa.try_move(msg.data):
                msg = Message(cmd=Commands.STATUS, data=200)
                self._send_reply(address, msg.serialize())
            else:
                msg = Message(cmd=Commands.STATUS, data=400)
                self._send_reply(address, msg.serialize())

        # robo estabelece conexao com o seu respectivo supervisor
        elif msg.cmd == Commands.CONNECT_TO_SS:
            print("Robo Conectado")
            self.robot_address = address
            msg = Message(cmd=Commands.STATUS, data=200)
            self._send_reply(address, msg.serialize())

        elif msg.cmd == Commands.GET_FLAG:
            self.comunica_com_sa.get_flag(msg.data)
        else:
            pass
            # nada acontece, feijoada

    def _send_reply(self, address, msg):
        self.router_socket.send_multipart([address, msg])

    def send_bandeiras(self):
        msg = Message(cmd=Commands.UPDATE_FLAGS, data=self.comunica_com_sa.cacas)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])


    def _handle(self):
        while self.run_flag:
            events = dict(self.poller.poll())
            for event in events:
                address, req = self.router_socket.recv_multipart()
                msg = Message(address, req)
                self._process_cmd(msg)

    def move(self, coord):
        """Envia ao robo a ordem para se mover para coord"""
        info = {
            "status": 200,
            "data": coord
        }
        msg = Message(cmd=Commands.MOVE_TO, data=info)
        # TODO CORRIGIR ESSA PARTE
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])
        print("as coord sao", coord)

    def run(self):
        self.comunica_com_sa.start()
        self.comunica_com_sa.login()
        self._handle()


########################################################################################################################

if __name__ == '__main__':
    ip = sys.argv[1]
    name = sys.argv[2]
    print(ip, name)
    comsa = ComunicaComSA(ip, Commands.PORT_SA, name)
    supervisor = Supervisor(comsa)
    supervisor.start()
    comsa.set_supervisor(supervisor)


