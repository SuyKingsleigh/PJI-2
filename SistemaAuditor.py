import socket
from threading import Thread
from Public import Message, Commands

import zmq, random


########################################################################################################################

class Jogador:
    '''Classe Jogador: Representa um jogador
    contem sua pontuacao, socket(dealer), posicao, pontuacao e IP do SS
    '''
    def __init__(self, **kwargs):
        self.id = self._get(kwargs, 'id', None)
        self.socket = self._get(kwargs, 'socket', None)
        self.pos = self._get(kwargs, 'pos', (None, None))
        self.ip = self._get(kwargs, 'ip', None)
        self.score = 0


    def increase_score(self):
        '''Atualiza a pontuacao do jogador'''
        self.score = self.score + 1

    def _get(self,kwargs,key, defval):
        try:
            return kwargs[key]
        except:
            return defval

    def set_pos(self, coord):
        '''Atualiza/Define a posicao do jogador'''
        self.pos = coord

    def set_ip(self, ip):
        '''Atualiza/Define o IP do jogador'''
        self.ip = ip


########################################################################################################################


class Jogo:
    """
        Classe Responsavel pelo jogo, ou seja:
        >Sorteia as cacas
        >Verifica a validade das cacas
        >Controla
        >gerencia mapa
        >a posição atual onde está cada robô e aposição para a qual cada robô deverá se deslocar na sua primeira movimentação.
    """

    DIMENSAO = 6 # dimensao do mapa, no NxN
    NUMERO_DE_CACAS = 3 # numero de cacas no mapa

    # jogadores_dict: Dict[zmq.Socket, Jogador]

    def __init__(self):
        # Supondo que o mapa e numero de cacas sejam estaticos.
        self.dimensao = Jogo.DIMENSAO
        self.numero_de_cacas = Jogo.NUMERO_DE_CACAS

        self.lista_de_cacas = []  # lista das cacas
        self.jogador_pos = dict()  # dicionario da posicao de cada jogador {socket : (coordX, coordY) }
        self.jogadores_dict = dict()

    def sorteia_cacas(self):
        """Sorteia as cacas, retorna uma lista com n cacas, dispostas em tuplas (coordX, coordY)"""
        self.lista_de_cacas = []
        i = 0
        while i != self.numero_de_cacas:
            x, y = random.randint(0, self.dimensao - 1), random.randint(0, self.dimensao - 1)
            if (x, y) not in self.lista_de_cacas:
                self.lista_de_cacas.append((x, y))
                i = i + 1

        return self.lista_de_cacas


    def registra_jogador(self, socket, kwargs):
        """Registra o jogador, caso a ID solicitada JA esteja em uso, retorna falso"""
        id = kwargs['id']
        ip = kwargs['ip']
        print("Registra_jogador, id = ", id, " ip= ", ip)
        for player in self.jogadores_dict.values():
            if id == player.id:
                return False
        else:
            self.jogadores_dict[socket] = Jogador(socket=socket, id=id, ip=ip)
            return True

    def verifica_cacas(self, cacas):
        """Retorna true e remove da lista de cacas quando a caca eh valida, false caso contrario
         """
        if cacas in self.lista_de_cacas:
            self.lista_de_cacas.remove(cacas)
            return True
        return False

    def inicia_partida(self):
        """
        Sorteia as posicoes inicias de cada Robo
        Retorna um dicionario: {socket : (coord_inicial_X, coord_inicial_Y) }
        """
        self.jogador_pos = dict()
        for socket in self.jogadores_dict.keys():
            # Fica sorteando valores, se o valor NAO estiver em jogador_pos nem em lista_de_cacas, adiciona e vai pro proximo jogador
            while True:
                x, y = random.randint(0, self.dimensao - 1), random.randint(0, self.dimensao - 1)
                if (x, y) not in (self.jogador_pos.values() and self.lista_de_cacas):
                    self.jogador_pos[socket] = (x, y)
                    self.jogadores_dict[socket].set_pos((x, y))
                    break

        return self.jogador_pos

    def move_jogador(self, socket_jogador, coord):
        coord = tuple(coord)
        if coord > (0, 0):
            if coord not in self.jogador_pos.values():
                self.jogador_pos[socket_jogador] = coord
                self.jogadores_dict[socket_jogador].set_pos(coord)
                print("Jogador: ", self.jogadores_dict[socket_jogador].id, " esta indo para ", self.jogadores_dict[socket_jogador].pos)
                return True

        return False

    def stop(self):
        """"Para a partida porem mantem os jogadores cadastrados
            Zera o placar dos jogadores.
        """
        player_score_dict = dict()
        for jogador in self.jogadores_dict.values():
            player_score_dict[jogador.id] = jogador.score
            jogador.score = 0

        return player_score_dict


    def get_player_ip(self, id):
        for player in self.jogadores_dict.values():
            if player.id == id:
                return player.ip

    def get_players_pos(self):
        pos_list = []
        for jogador in self.jogadores_dict.values(): pos_list.append(jogador.pos)
        return pos_list




########################################################################################################################

class Auditor:
    """
        Classe InterfaceAuditor, eh a classe responsavel pela comunicacao do arbitro com os SS

        Uma thread sera para coisas automaticas do sistema, como atualizacao de mapa e etc

        Publish:
        Socket para o broadcast

        {cmd='start',(x,y)} tamanho do mapa X por Y
        {cmd='cacas', lista de tuplas das cacas} envia a posicao de todas as cacas para os SS cadastrados
        {cmd=obteve_caca, (id_robo, [coorX,coordY]} informa a todos SS cadastrados que algum robo obteve alguma caca

         Router:
         Socket para atender soliticacoes individuais de cada SS, e atende, exclusivamente, a solicitacao de IP do SR.

    """

    def __init__(self, port):
        self.port = port

        # cria os sockets
        self._context = zmq.Context()
        self._publish_socket = self._context.socket(zmq.PUB)
        self._router_socket = self._context.socket(zmq.ROUTER)

        # coisa os sockets
        self._publish_socket.bind("tcp://*:%s" % str(self.port))  # apenas para o broadcast
        self._router_socket.bind("tcp://*:%s" % str(self.port + 1))  # apenas para solicitacoes individuais

        # poller
        self._poller = zmq.Poller()
        self._poller.register(self._router_socket, zmq.POLLIN)  # notifica cada mensagem recebida

        # Jogo
        self.jogo = Jogo()
        self.cacas = []
        self.jogo_started = False
        self.thread_run_flag = True

        # imprime o ip do servidor para facilitar a vida
        print("O ip do servidor eh ", self._get_my_ip(), "\n")

    def _get_my_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.my_ip = s.getsockname()[0]
        try:
            s.close()
        except Exception as e:
            pass
        return self.my_ip

    # Processa as requisicoes individuais de cada S.S.
    def _process_request(self, msg):
        print("msg.cmd:  ", msg.cmd)
        # cadastra o S.S
        if msg.cmd == Commands.LOGIN:
            if self.jogo.registra_jogador(msg.address, msg.data):
                print(msg.data)
                info = {'status': 200, 'info': 'logado'}
                self._send_status(info, msg.address)
                print("Login de ", msg.data, " efetuado com sucesso")
            else:
                info = {'status': 400, 'info': 'nao foi possivel logar'}
                self._send_status(info, msg.address)

        # autoriza ou nao o movimento de um jogador
        elif msg.cmd == Commands.MOVE_TO:
            if self.jogo.move_jogador(msg.address, msg.data):
                info = {'status': 200, 'info': 'OK'}
                self._send_status(info, msg.address)
                self._update_map()

            else:
                info = {'status': 400, 'info': 'posicao invalida ou ja ocupada'}
                self._send_status(info, msg.address)

        # valida ou nao uma caca, caso seja validada, envia a todos a nova lista de cacas
        # atualiza placar tb
        elif msg.cmd == Commands.GET_FLAG:
            coord = tuple(msg.data)
            print("get_flag", coord)
            if self.jogo.verifica_cacas(coord):
                self.jogo.jogadores_dict[msg.address].increase_score()
                self._update_flags()
                print("O jogador", self.jogo.jogadores_dict[msg.address].id, "obteve a caca em ", coord, " sua pontuacao eh ", self.jogo.jogadores_dict[msg.address].score)
            else:
                print("falhou ")

        elif msg.cmd == Commands.GET_IP:
            ip = self.jogo.get_player_ip(msg.data)
            rep = Message(cmd=Commands.GET_IP, data=ip)
            self._router_socket.send_multipart([msg.address, rep.serialize()])
        else:
            pass

    def _update_map(self):
        rep = Message(cmd=Commands.UPDATE_MAP, data=self.jogo.get_players_pos())
        self._publish_socket.send(rep.serialize())

    def _update_flags(self):
        # atualiza as cacas
        msg = Message(cmd=Commands.UPDATE_FLAGS, data=self.jogo.lista_de_cacas)
        self._publish_socket.send(msg.serialize())

    def _send_status(self, info, address):
        resp = Message(cmd=Commands.STATUS, data=info)
        self._router_socket.send_multipart([address, resp.serialize()])

    def inicia_partida(self):
        """Sorteia cacas do jogo, envia a lista das cacas para todos os robos
           Sorteia posicao inicial de cada um, envia a posicao individualmente
           cmd=start
           """
        self._sorteia_cacas()
        self._sorteia_posicao_inicial()
        self.jogo_started = True  # seta a flag de started pra true

    def _sorteia_cacas(self):
        # Sorteia e envia as bandeiras
        self.cacas = self.jogo.sorteia_cacas()
        msg = Message(cmd=Commands.START, data=self.cacas)
        print("Bandeiras: ", self.cacas)
        self._publish_socket.send(msg.serialize())

    def _sorteia_posicao_inicial(self):
        # Sorteia e envia as posicoes iniciais
        self.jogadores_pos = self.jogo.inicia_partida()
        for socket in self.jogadores_pos.keys():
            msg = Message(cmd=Commands.POS, data=self.jogadores_pos[socket])
            self._router_socket.send_multipart([socket, msg.serialize()])
            print("Posicao inicial do jogador ", self.jogo.jogadores_dict[socket].id, " eh ",
                  self.jogadores_pos[socket])

    def stop_game(self):
        msg = Message(cmd=Commands.STOP)
        self._publish_socket.send(msg.serialize())
        placar = self.jogo.stop()
        print("o jogo terminou")
        for player in placar:
            print("o jogador ", player, " obteve ", placar[player])

        self.jogo_started = False

    def stop_thread(self):
        self.thread_run_flag = False
        self.daemon.join(timeout=1000)

    # lida com a recepcao de mensagens
    def _handle(self):
        while self.thread_run_flag:
            events = dict(self._poller.poll(timeout=None))  # dicionario = {SOCKET : EVENTO}
            for event in events:
                address, req = self._router_socket.recv_multipart()
                msg = Message(address, req)
                self._process_request(msg)

    def run(self):
        self.daemon = Thread(target=self._handle)
        self.daemon.start()

########################################################################################################################

class InterfaceAuditora:
    def __init__(self, port):
        self.auditor = Auditor(port)
        self.auditor.run()

    def _read_commands(self, command):
        if command == Commands.START:
            self.auditor.inicia_partida()
        elif command == Commands.STOP:
            pass
        # Todo criar metodo de parada em auditor
        else:
            print("O comando ", command, " eh invalido")

    def run(self):
        user_input = ' '
        while not user_input == Commands.QUIT:
            user_input = input("> ")
            if user_input == Commands.START:
                self.auditor.inicia_partida()
            elif user_input == Commands.QUIT:
                self.auditor.stop_game()
            else:
                pass
        self.auditor.stop_thread()
        print("Fim")



########################################################################################################################
if __name__ == "__main__":
    joguineo = InterfaceAuditora(Commands.PORT_SA)
    joguineo.run()
