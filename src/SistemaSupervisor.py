
import os
import signal
import socket
import sys
from threading import *

import zmq
from Public import Message, Commands, Mover


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
        self.blocked = False

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
            print("Posicao inicial: ", self.pos)
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
            self.supervisor.set_mode(msg.data)
            if self.supervisor.mode:
                print("modo manual")
                if self.supervisor.jogo.is_alive():
                    # se a thread estiver executando, para e reinicia
                    try:
                        self.supervisor.jogo.join()
                        self.supervisor.start_interface(msg.data)
                    except Exception as e:
                        print("falhou ao reiniciar a thread do manual", e)
                else:
                    self.supervisor.start_interface(msg.data)

            else:
                print("modo automatico")
                self.supervisor.jogo.manual = msg.data  # seta como false


        elif msg.cmd == Commands.STOP:
            self.supervisor.stop()
            self.try_move(self.supervisor.begin_pos)
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

    def get_flag(self, coord):
        """ Envia mensagem que obteve uma bandeira """
        req = Message(cmd=Commands.GET_FLAG, data=coord)
        self.dealer_socket.send(req.serialize())
        if self.supervisor.jogo.manual:
            Thread(target=self._wait_flag_status, daemon=False).start()
        else:
            self._wait_flag_status()

    def _wait_flag_status(self):

        ## bloqueia tanto interface de jogo quanto supervisor
        self.supervisor.jogo.block()
        self.supervisor.block()

        while True:
            resp = self.dealer_socket.recv()
            resp = Message(0, resp)
            if resp.cmd == Commands.STATUS_GET_FLAG:
                break
        # desbloqueia ambos
        self.supervisor.unblock()
        self.supervisor.jogo.unblock()


########################################################################################################################

class Supervisor(Thread):
    SUPERVISOR_PORT = 9999  # porta

    """Interface que faz a comunicacao entre o SR e o proprio sistema, camada mais abaixo do SS"""

    def __init__(self, comunica_com_sa, initial_pos):
        super().__init__()
        # self.daemon = True

        # cria interface para comunicacao com o sistema AUDITOR
        self.comunica_com_sa = comunica_com_sa

        # socket para comunicar com o SISTEMA EXPLORADOR
        self.context = zmq.Context()
        self.router_socket = self.context.socket(zmq.ROUTER)
        self.router_socket.bind("tcp://*:%s" % str(Supervisor.SUPERVISOR_PORT))

        # poller
        self.poller = zmq.Poller()
        self.poller.register(self.router_socket, zmq.POLLIN)  # notifica cada mensagem recebida

        self.mode = None
        self.run_flag = True
        self.begin_pos = initial_pos
        self.current_pos = initial_pos
        self.robot_address = None

        self.jogo = InterfaceDeJogo(self)
        self.name = "supervisor"
        self.blocked = False

    def send_updated_map(self, map):
        msg = Message(cmd=Commands.UPDATE_MAP, data=map)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])

    def block(self):
        self.blocked = True

    def unblock(self):
        self.blocked = False

    def is_blocked(self):
        return self.blocked

    def _process_cmd(self, msg):
        address = msg.address
        # recebe mensagem de obtem bandeira
        if msg.cmd == Commands.GET_FLAG:
            self.comunica_com_sa.get_flag(msg.data)
            while self.is_blocked(): pass
            # o robo n precisa saber o status, so o supervisor
            self.router_socket.send_multipart([self.robot_address, Message(cmd=Commands.STATUS_GET_FLAG).serialize()])

        # robo informa ao supervisor que quer ir para X,Y posicao
        elif msg.cmd == Commands.MOVE_TO:
            self.current_pos = msg.data
            self.comunica_com_sa.try_move(msg.data)


        # robo estabelece conexao com o seu respectivo supervisor
        elif msg.cmd == Commands.CONNECT_TO_SS:
            print("Robo Conectado")
            self.robot_address = address
            msg = Message(cmd=Commands.INITIAL_POS, data=self.begin_pos)
            self._send_reply(address, msg.serialize())

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

    def start_robot(self):
        msg = Message(cmd=Commands.START)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])
        # self.manda_frente()

    def stop(self):
        msg = Message(cmd=Commands.STOP)
        self.router_socket.send_multipart([self.robot_address, Message(cmd=Commands.STOP).serialize()])
        self.current_pos = self.begin_pos
        print("[STOPPED] begin pos is: ", self.begin_pos)

    def move(self, coord):
        """Envia ao robo a ordem para se mover para coord"""
        info = {
            "status": 200,
            "data": coord
        }
        msg = Message(cmd=Commands.MOVE_TO, data=info)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])
        self.current_pos = coord
        print("as coord sao", self.current_pos)

    def run(self):
        self.comunica_com_sa.start()
        self.comunica_com_sa.login()
        self._handle()

    def manda_frente(self):
        msg = Message(cmd=Commands.DIRECTION, data=Mover.FRENTE)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])
        self.current_pos = int(self.current_pos[0]) + 1, int(self.current_pos[1])
        print("frente")
        print("\n", self.current_pos)

    def manda_tras(self):
        msg = Message(cmd=Commands.DIRECTION, data=Mover.TRAS)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])
        self.current_pos = int(self.current_pos[0]) - 1, int(self.current_pos[1])
        print("tras")
        print("\n", self.current_pos)

    def manda_direita(self):
        msg = Message(cmd=Commands.DIRECTION, data=Mover.DIREITA)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) + 1
        print("direita")
        print("\n", self.current_pos)

    def manda_esquerda(self):
        msg = Message(cmd=Commands.DIRECTION, data=Mover.ESQUERDA)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])
        self.current_pos = int(self.current_pos[0]), int(self.current_pos[1]) - 1
        print("esquerda")
        print("\n", self.current_pos)

    def start_interface(self, manual):
        self.jogo = InterfaceDeJogo(self)
        self.jogo.manual = manual
        self.jogo.start()

    def set_mode(self, mode):
        msg = Message(cmd=Commands.MODE, data=mode)
        self.router_socket.send_multipart([self.robot_address, msg.serialize()])


########################################################################################################################

class InterfaceDeJogo(Thread):
    def __init__(self, supervisor):
        super().__init__()
        self.supervisor = supervisor
        self.manual = self.supervisor.mode
        self.name = "interfacedejogo"
        self.blocked = False

    def set_auto(self):
        self.manual = False

    def set_manual(self):
        self.manual = True

    def _manual_input(self):
        user_input = input(">>> \n")
        if user_input == "w" and not self.blocked:
            if self.manual:
                self.supervisor.manda_frente()
            else:
                print("esta no modo automatico ou bloqueado")

        elif user_input == "d" and not self.blocked:
            if self.manual:
                self.supervisor.manda_direita()
            else:
                print("esta no modo automatico ou bloqueado")

        elif user_input == "a" and not self.blocked:
            if self.manual:
                self.supervisor.manda_esquerda()
            else:
                print("esta no modo automatico ou bloqueado")

        elif user_input == "s" and not self.blocked:
            if self.manual:
                self.supervisor.manda_tras()
            else:
                print("esta no modo automatico ou bloqueado")

        elif user_input == " " and not self.blocked:
            print("gettin flag at", self.supervisor.current_pos)
            self.supervisor.comunica_com_sa.get_flag(self.supervisor.current_pos)

        elif user_input == "q":
            if self.manual: pass
        else:
            pass

    def block(self):
        self.blocked = True
        print("[INTERFACE DE JOGO] BlOQUEADA")

    def unblock(self):
        self.blocked = False
        print("[INTERFACE DE JOGO] DESBLOQUEADA")

    def run(self):
        print("\n\nInterface de jogo\n\n")
        while self.manual: self._manual_input()


########################################################################################################################

if __name__ == '__main__':
    """PARAMETROS PARA TESTE EM LOCALHOST
    localhost jamal 0 0"""

    ip = sys.argv[1]
    name = sys.argv[2]
    initial_pos = sys.argv[3], sys.argv[4]

    comsa = ComunicaComSA(ip, Commands.PORT_SA, name)
    supervisor = Supervisor(comsa, initial_pos)

    # jogo = InterfaceDeJogo(supervisor)
    comsa.set_supervisor(supervisor)
    supervisor.start()

    while not supervisor.robot_address: pass