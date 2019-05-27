import socket
import sys
from datetime import time
from threading import Thread
from Public import Message, Commands
import time
import zmq, random


########################################################################################################################

class Jogador:
    '''Classe Jogador: Representa um jogador
    contem sua pontuacao, socket(dealer), posicao, pontuacao e IP do SS
    '''

    def __init__(self, **kwargs):
        self.id = self._get(kwargs, Commands.ID, None)
        self._socket = self._get(kwargs, 'socket', None)
        self.pos = self._get(kwargs, Commands.INITIAL_POS, None)
        self.ip = self._get(kwargs, Commands.IP, None)
        self.score = 0

    def increase_score(self):
        '''Atualiza a pontuacao do jogador'''
        self.score = self.score + 1

    def _get(self, kwargs, key, defval):
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

        atributo "manual": true se o jogo for manual, false se for automatico, vem por default true
    """

    DIMENSAO = 6  # dimensao do mapa, no NxN
    NUMERO_DE_CACAS = 3  # numero de cacas no mapa

    # jogadores_dict: Dict[zmq.Socket, Jogador]

    def __init__(self):
        # Supondo que o mapa e numero de cacas sejam estaticos.
        self.dimensao = Jogo.DIMENSAO
        self.numero_de_cacas = Jogo.NUMERO_DE_CACAS
        self.manual = True  # Modo de jogo, true se manual, false se automatico

        self.lista_de_cacas = []  # lista das cacas
        self._jogador_pos = dict()  # dicionario da posicao de cada jogador {socket : (coordX, coordY) }
        self._jogadores_dict = dict()

    def set_game_mode(self, mode):
        self.manual = mode

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
        id = kwargs[Commands.ID]
        ip = kwargs[Commands.IP]
        pos = kwargs[Commands.INITIAL_POS]
        print("Registra_jogador, id = ", id, " ip= ", ip, "pos= ", pos)
        for player in self._jogadores_dict.values():
            if id == player.id:
                return False
        else:
            self._jogadores_dict[socket] = Jogador(socket=socket, id=id, ip=ip, pos=pos)
            self._jogador_pos[socket] = pos
            return True

    def verifica_cacas(self, cacas):
        """Retorna true e remove da lista de cacas quando a caca eh valida, false caso contrario
         """
        if cacas in self.lista_de_cacas:
            self.lista_de_cacas.remove(cacas)
            return True
        return False

    # def inicia_partida(self):
    #     """
    #     Sorteia as posicoes inicias de cada Robo
    #     Retorna um dicionario: {socket : (coord_inicial_X, coord_inicial_Y) }
    #     """
    #     self.jogador_pos = dict()
    #     for socket in self.jogadores_dict.keys():
    #         # Fica sorteando valores, se o valor NAO estiver em jogador_pos nem em lista_de_cacas, adiciona e vai pro proximo jogador
    #         while True:
    #             x, y = random.randint(0, self.dimensao - 1), random.randint(0, self.dimensao - 1)
    #             if (x, y) not in (self.jogador_pos.values() and self.lista_de_cacas):
    #                 self.jogador_pos[socket] = (x, y)
    #                 self.jogadores_dict[socket].set_pos((x, y))
    #                 break
    #
    #     return self.jogador_pos

    def move_jogador(self, socket_jogador, coord):
        """Atualiza a posicao do jogador"""
        coord = tuple(coord)
        if coord > (0, 0):
            if coord not in self._jogador_pos.values():
                self._jogador_pos[socket_jogador] = coord
                self._jogadores_dict[socket_jogador].set_pos(coord)
                print("Jogador: ", self._jogadores_dict[socket_jogador].id, " esta indo para ",
                      self._jogadores_dict[socket_jogador].pos)
                return True

        return False

    def stop(self):
        """"Para a partida porem mantem os jogadores cadastrados
            Zera o placar dos jogadores.
        """
        player_score_dict = dict()
        for jogador in self._jogadores_dict.values():
            player_score_dict[jogador.id] = jogador.score
            jogador.score = 0

        return player_score_dict

    def get_player_ip(self, id):
        """Retorna a pontuacao do jogador
        ID = nome do jogador"""
        for player in self._jogadores_dict.values():
            if player.id == id:
                return player.ip

    def update_map(self):
        """Retorna uma lista de posicao, com a posicao de cada jogador, ou seja, apenas as coord ocupadas"""
        pos_list = []
        for jogador in self._jogadores_dict.values(): pos_list.append(jogador.pos)
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
        """
        cmd=Login -> resposta; cmd=STATUS ; data = 200 ou 400
        cmd=Move_To -> resposta: nenhuma
        cmd=get_flag -> resposta:cmd=status ; data = 200 ou 400
        cmd=get_ip -> resposta: cmd=get_ip ; data= ip
        """
        print("msg.cmd:  ", msg.cmd)
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
                # info = {'status': 200, 'info': 'OK'}
                # self._send_status(info, msg.address)
                self._update_map()
            else:
                info = {'status': 400, 'info': 'posicao invalida ou ja ocupada'}
                self._send_status(info, msg.address)

        # valida ou nao uma caca, caso seja validada, envia a todos a nova lista de cacas
        # atualiza placar tb
        # envia uma mensagem individual ao jogador, liberando seu movimento.
        elif msg.cmd == Commands.GET_FLAG:
            self._process_flag_request(msg)

        elif msg.cmd == Commands.GET_IP:
            ip = self.jogo.get_player_ip(msg.data)
            rep = Message(cmd=Commands.GET_IP, data=ip)
            self._router_socket.send_multipart([msg.address, rep.serialize()])
        else:
            pass

    def _update_map(self):
        msg = Message(cmd=Commands.UPDATE_MAP, data=self.jogo.update_map())
        self._publish_socket.send(msg.serialize())

    def _update_flags(self):
        # atualiza as cacas
        msg = Message(cmd=Commands.UPDATE_FLAGS, data=self.jogo.lista_de_cacas)
        self._publish_socket.send(msg.serialize())

    def _send_status(self, info, address):
        resp = Message(cmd=Commands.STATUS, data=info)
        self._router_socket.send_multipart([address, resp.serialize()])

    def _process_flag_request(self, msg):
        validate = Thread(target=self._validate_flag_request, args=[msg])
        validate.daemon = False
        validate.start()

    def _validate_flag_request(self, *args):
        msg = args[0]
        coord = tuple(msg.data)
        print("get_flag", coord)
        # if self.jogo.verifica_cacas(coord):
        if coord in self.jogo.lista_de_cacas:
            user_input = input("\na caca eh valida, digite duas vezes 'ok' para confirmar, qualquer outra coisa para nao validar\n")
            if user_input == 'ok':
                # Caca autorizada, envia status ok
                print("O jogador", self.jogo._jogadores_dict[msg.address].id, "obteve a caca em ", coord,
                      " sua pontuacao eh ", self.jogo._jogadores_dict[msg.address].score)
                ans = Message(cmd=Commands.STATUS_GET_FLAG,data=200)
                self._router_socket.send_multipart([msg.address, ans.serialize()])

                # incrementa pontuacao
                self.jogo._jogadores_dict[msg.address].increase_score()
                self.jogo.verifica_cacas(coord) # atualiza a lista de bandeiras
                self._update_flags() # envia mensagem com a lista de bandeiras atualizadas
                print("sent")
        else:
            user_input = input("\nah caca eh invalida, digite  duas vezes 'ok' para confirmar\n")
            if user_input == 'ok':
                print("falhou ao obter a bandeira")
                ans = Message(cmd=Commands.STATUS_GET_FLAG,data=200)
                self._router_socket.send_multipart([msg.address, ans.serialize()])
                print("sent")


    def inicia_partida(self):
        """Sorteia cacas do jogo, envia a lista das cacas para todos os robos
           Sorteia posicao inicial de cada um, envia a posicao individualmente
           cmd=start
           """
        # self.set_mode(Commands.MANUAL)
        self._sorteia_cacas()
        self._sorteia_posicao_inicial()
        self.jogo_started = True  # seta a flag de started pra true

    def set_mode(self, mode):
        """Manual = TRUE
           Automatico = False """
        self.jogo.manual = mode
        msg = Message(cmd=Commands.MODE, data=mode)
        self._publish_socket.send(msg.serialize())
        if mode: print("modo manual")

    def _sorteia_cacas(self):
        # Sorteia e envia as bandeiras
        self.cacas = self.jogo.sorteia_cacas()
        msg = Message(cmd=Commands.START, data=self.cacas)
        print("Bandeiras: ", self.cacas)
        self._publish_socket.send(msg.serialize())

    def _sorteia_posicao_inicial(self):
        # Sorteia e envia as posicoes iniciais
        # self.jogadores_pos = self.jogo._jogador_pos
        # for socket in self.jogadores_pos.keys():
        #     msg = Message(cmd=Commands.POS, data=self.jogadores_pos[socket])
        #     self._router_socket.send_multipart([socket, msg.serialize()])
        #     print("Posicao inicial do jogador ", self.jogo._jogadores_dict[socket].id, " eh ",
        #           self.jogadores_pos[socket])
        pass

    def stop_game(self):
        """Termina a partida, imprime o placar, informa aos supervisores o fim da mesma """
        msg = Message(cmd=Commands.STOP)
        self._publish_socket.send(msg.serialize())
        placar = self.jogo.stop()
        print("o jogo terminou")
        for player in placar:
            print("o jogador ", player, " obteve ", placar[player])

        self.jogo_started = False

    def stop_thread(self):
        """Termina a thread responsavel por lidar com requisicoes dos supervisores"""
        self.thread_run_flag = False
        self.daemon.join(timeout=1)

    # lida com a recepcao de mensagens
    def _handle(self):
        while self.thread_run_flag:
            events = dict(self._poller.poll(timeout=None))  # dicionario = {SOCKET : EVENTO}
            for event in events:
                address, req = self._router_socket.recv_multipart()
                print(req)
                msg = Message(address, req)
                self._process_request(msg)

    def quit(self):
        msg = Message(cmd=Commands.QUIT)
        self._publish_socket.send(msg.serialize())

    def run(self):
        """Inicia a thread para lidar com requisicoes dos supervisores """
        self.daemon = Thread(target=self._handle, name="auditor run")
        self.daemon.daemon = True
        self.daemon.start()


########################################################################################################################

class InterfaceAuditora:
    """Uma interface em modo texto, cuja funcionalidade eh apenas iniciar partidas, terminar partidas e terminar a execucao
    deste mesmo sistema
    """

    def __init__(self, port):
        self.auditor = Auditor(port)
        self.auditor.run()

    def run(self):
        """le a entrada padrao
        start = inicia partida
        stop = termina partida, informa placar, resta placar e prepara-se para uma proxima
        q = finaliza partida (feito pra testes)
        """
        user_input = ' '
        while not user_input == Commands.QUIT:
            user_input = input("> ")
            if user_input == Commands.START:
                self.auditor.inicia_partida()
            elif user_input == Commands.QUIT:
                self.auditor.stop_game()
                self.auditor.stop_thread()
                self.auditor.quit()
                sys.exit()
            elif user_input == Commands.STOP:
                self.auditor.stop_game()
            elif user_input == "manual":
                self.auditor.set_mode(Commands.MANUAL)
            elif user_input == "automatico":
                self.auditor.set_mode(Commands.AUTOMATICO)
            else:
                pass
        print("Fim")


########################################################################################################################
if __name__ == "__main__":
    joguineo = InterfaceAuditora(Commands.PORT_SA)
    joguineo.run()
