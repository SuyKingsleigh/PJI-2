from manual import *
from automatico import *
from mover import *
# from mover_test import *
from shared import *
from receptor import *
from transmissor import *
from time import sleep
from threading import Thread
import json

class ModoDeJogo(object):
	MANUAL = 1
	AUTOMATICO = 2


class InterfaceSR(Thread):
	"""World interface for SR"""

	def __init__(self):
		self.modo = None
		self.cacas = []
		self.cacador = None
		# self.mac = self._get_mac()
		self.mac = "aa:bb:cc:dd:ee:ff"
		self._ler_cadastro()
		#self.identidade = self._get_mac()

		super(InterfaceSR, self).__init__()


	def _get_mac(self):
		mac = ""
		with open('/sys/class/net/wlan0/address', 'r') as f:
			mac = f.readline().rstrip()
		f.close()
		return mac


	def _ler_cadastro(self):
		try:
			with open('cadastro.cfg') as f:
				cadastro = json.load(f)
				self.cor = cadastro['cor']
				self.nome = cadastro['nome']
		except:
			self.cor = 0
			self.nome = "Grupo3"

	def get_cor(self):
		return self.cor


	def fim_jogo(self):
		global shared_obj
		if self.modo == ModoDeJogo.AUTOMATICO:
			shared_obj.set(SharedObj.InterfaceFimJogo, 1)
		else:
			shared_obj.set(SharedObj.InterfaceFimJogo, 1)
			shared_obj.set(SharedObj.ManualMovimento, Mover.EXIT)


	def _limpa_var_globais(self):
		global shared_obj
		shared_obj.set(SharedObj.MoverMovimento, Mover.PARADO)
		shared_obj.set(SharedObj.MoverHistorico, [])
		shared_obj.clear_event(SharedObj.MoverCoordenadaEvent)
		shared_obj.set(SharedObj.MoverCoordenada, self.coord_inicial)
		shared_obj.set(SharedObj.ManualMovimento, Mover.PARADO)
		shared_obj.set(SharedObj.AutomaticoValidarCaca, 0)
		shared_obj.set(SharedObj.InterfaceRespValidaCacaMsg, {})
		shared_obj.set(SharedObj.InterfaceNovasCacas, 0)
		shared_obj.clear_event(SharedObj.InterfaceRespValidaCacaEvent)
		shared_obj.set(SharedObj.InterfaceFimJogo, 0)
		shared_obj.set(SharedObj.InterfaceCacasAtualizadas, [])
		shared_obj.set(SharedObj.InterfacePauseContinua, 0)


	def novo_jogo(self, msg):
		global shared_obj

		ret = {'cmd': MsgSRtoSS.NovoJogoConfigurado, 'ack': 0}
		if 'modo_jogo' not in msg:
			ret['erro'] = MsgRoboErro.ParametroNaoInformado
			ret['param'] = 'modo_jogo'
			return ret
		else:
			self.modo_jogo = msg['modo_jogo']

		if 'x' not in msg:
			ret['erro'] = MsgRoboErro.ParametroNaoInformado
			ret['param'] = 'x'
			return ret
		elif 'y' not in msg:
			ret['erro'] = MsgRoboErro.ParametroNaoInformado
			ret['param'] = 'y'
			return ret
		else:
			self.coord_inicial = (msg['x'], msg['y'])

		if msg['modo_jogo'] == ModoDeJogo.AUTOMATICO:
			if 'cacas' not in msg:
				ret['erro'] = MsgRoboErro.ParametroNaoInformado
				ret['param'] = 'cacas'
				return ret
			else:
				self.cacas = []
				for caca in msg['cacas']:
					self.cacas.append((caca['x'], caca['y']))

		self._limpa_var_globais()

		if self.modo_jogo == ModoDeJogo.MANUAL:
			shared_obj.set(SharedObj.ManualMovimento, Mover.PARADO)
			self.cacador = Manual(self.coord_inicial)

		elif self.modo_jogo == ModoDeJogo.AUTOMATICO:
			cacas = msg['cacas']
			self.cacador = Automatico(self.coord_inicial, self.cacas)

		ret['ack'] = 1
		return ret


	def mover_manual(self, direcao):
		global shared_obj
		if self.modo == ModoDeJogo.AUTOMATICO:
			print("Modo de jogo automatico, sem movimentos manuais!!")
			return

		shared_obj.set(SharedObj.ManualMovimento, direcao)


	def _atualiza_cacas(self, cacas):
		global shared_obj
		new_cacas = []
		for caca in cacas:
			new_cacas.append((caca['x'], caca['y']))

		old_cacas = shared_obj.get(SharedObj.InterfaceCacasAtualizadas)
		if new_cacas != old_cacas:
			shared_obj.set(SharedObj.InterfaceCacasAtualizadas, new_cacas)
			shared_obj.set(SharedObj.InterfaceNovasCacas, 1)


	def _atualiza_pos_adv(self, pos):
		# TODO
		pass

	def _atualiza_cadastro(self):
		cadastro = {'cor': self.cor, 'nome': self.nome}
		with open('cadastro.cfg', 'w') as f:
			json.dump(cadastro, f)

	def cadastra_robo(self, msg):
		if 'cor' not in msg:
			return

		self.cor = msg['cor']
		self.nome = msg['nome'] if 'nome' in msg else 'Grupo3'
		self._atualiza_cadastro()

	def atualiza_mapa(self, msg):
		if 'cacas' in msg:
			self._atualiza_cacas(msg['cacas'])

		if 'posicao_adversario' in msg:
			self._atualiza_pos_adv(msg['posicao_adversario'])

	def get_status(self):
		global shared_obj
		return shared_obj.get(SharedObj.MoverMovimento)


	def get_historico(self):
		global shared_obj
		historico = shared_obj.get(SharedObj.MoverHistorico)
		resp = {'cmd': MsgSRtoSS.SolicitaHistorico_RESP, 'historico': historico}
		self._envia_msg(resp)


	def pause(self):
		global shared_obj
		shared_obj.set(SharedObj.InterfacePauseContinua, 1)

	def continua(self):
		global shared_obj

		# Se mandar continuar, sem estar em pausa, nao faz nada
		if not shared_obj.get(SharedObj.InterfacePauseContinua):
			return

		shared_obj.set(SharedObj.InterfacePauseContinua, 0)

	def stop(self):
		self.pause()
		self.fim_jogo()


	def _envia_msg(self, msg):
		global shared_obj
		shared_obj.set(SharedObj.TransmitirLock, msg)
		shared_obj.set_event(SharedObj.TransmitirEvent)


	def run(self):
		global shared_obj
		print("##### ROBO INICIALIZADO #####")
		print("Nome: %s | Cor: %s\n" % (str(self.nome), str(self.cor)))

		while True:
			# Espera alguma mensagem ...
			shared_obj.wait_event(SharedObj.InterfaceEvent)

			shared_obj.acquire(SharedObj.InterfaceEventMsg)
			msg = shared_obj.get_directly(SharedObj.InterfaceEventMsg)
			if 'cmd' not in msg:
				continue

			cmd = msg['cmd']

			# Mensagens vindas do SS:
			if cmd == MsgSStoSR.SolicitaID:
				print("[RECEBIDO]: SolicitaID")
				resp = {'cmd': MsgSRtoSS.SolicitaID_Resp}
				resp['cor'] = self.cor
				resp['nome'] = self.nome
				resp['mac'] = self.mac
				self._envia_msg(resp)

			elif cmd == MsgSStoSR.NovoJogo:
				print("[RECEBIDO]: NovoJogo")
				resp = self.novo_jogo(msg)
				self._envia_msg(resp)

			elif cmd == MsgSStoSR.IniciaJogo:
				print("[RECEBIDO]: IniciaJogo")
				self.cacador.start()

			elif cmd == MsgSStoSR.Pausa:
				print("[RECEBIDO]: Pausa")
				self.pause()

			elif cmd == MsgSStoSR.Continua:
				print("[RECEBIDO]: Continua")
				self.continua()

			elif cmd == MsgSStoSR.FimJogo:
				print("[RECEBIDO]: FimJogo")
				self.fim_jogo()

			elif cmd == MsgSStoSR.Mover:
				print("[RECEBIDO]: Mover")
				if 'direcao' in msg and \
					self.modo_jogo is ModoDeJogo.MANUAL:
					self.mover_manual(msg['direcao'])

			elif cmd == MsgSStoSR.AtualizaMapa:
				print("[RECEBIDO]: AtualizaMapa")
				self.atualiza_mapa(msg)

			elif cmd == MsgSStoSR.ValidacaoCaca:
				print("[RECEBIDO]: ValidacaoCaca")
				shared_obj.set(SharedObj.InterfaceRespValidaCacaMsg, msg)
				shared_obj.set_event(SharedObj.InterfaceRespValidaCacaEvent)

			elif cmd == MsgSStoSR.SolicitaHistorico:
				print("[RECEBIDO]: SolicitaHistorico")
				self.get_historico()

			elif cmd == MsgSStoSR.CadastraRobo:
				print("[RECEBIDO]: CadastraRobo")
				self.cadastra_robo(msg)

			elif cmd == MsgSStoSR.SolicitaStatus:
				print("[RECEBIDO]: SolicitaStatus")
				resp = {'cmd': MsgSRtoSS.SolicitaStatus_RESP}
				self._envia_msg(resp)

			# Mensagens internas (do proprio SR)
			elif cmd == MsgSRtoSS.MovendoPara or \
				cmd == MsgSRtoSS.PosicaoAtual or \
				cmd == MsgSRtoSS.ValidaCaca or \
				cmd == MsgSRtoSS.ObstaculoEncontrado:
				self._envia_msg(msg)

			else:
				pass

			shared_obj.release(SharedObj.InterfaceEventMsg)
			shared_obj.clear_event(SharedObj.InterfaceEvent)

if __name__ == "__main__":
	t = Transmissor("192.168.0.101")
	t.start()

	r = Receptor("192.168.0.101")
	r.start()

	i = InterfaceSR()
	i.start()

	# for cmd in range (1000, 1004):
	# 	print("ENTER PARA ENVIAR MENSAGEM AO SS")
	# 	input()

	# 	msg = {'cmd': cmd}
	# 	shared_obj.set(SharedObj.TransmitirLock, msg)
	# 	shared_obj.set_event(SharedObj.TransmitirEvent)

	# 	sleep(2)

