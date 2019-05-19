# from mover_test import *
from mover import *
from interface import *
from threading import Thread, Lock
from shared import *
from time import sleep
from copy import deepcopy
from mensagens_robo import *
from receptor import *
from transmissor import *

class Automatico(Thread):
	"""Busca cacas de maneira autonoma"""
	def __init__(self, coord, cacas):
		global shared_obj
		self.posicao_inicial = coord
		self.cacas = cacas
		self.cacas_ordenadas = cacas
		self.cacas_encontradas = [] 
		self.historico_mov = []
		self._x = coord[0]
		self._y = coord[1]
		self._ultima_dir = Mover.FRENTE

		self.movedor = Mover(self._x, self._y)
		self.movedor.start()
		shared_obj.set(SharedObj.InterfaceCacasAtualizadas, cacas)

		super(Automatico, self).__init__()


	def _ordena_cacas(self):
		if self.posicao_inicial == (6, 6):
			self.cacas_ordenadas.sort(reverse=True)
		else:
			self.cacas_ordenadas.sort()


	def _calcula_direcoes(self, proxima_coord):
		direcoes = []
		if self.posicao_inicial == (0,0):
			offset_x = proxima_coord[0] - self._x
			offset_y = proxima_coord[1] - self._y
		else:
			offset_x = self._x - proxima_coord[0]
			offset_y = self._y - proxima_coord[1]

		# Calcula novas direcoes, tentando fazer menos curva
		if self._ultima_dir == Mover.TRAS:
			if offset_y < 0:
				for i in range(offset_y, 0):
					direcoes.append(Mover.TRAS)
			if offset_x > 0:
				for i in range(0, offset_x):
					direcoes.append(Mover.DIREITA)
			if offset_x < 0:
				for i in range(offset_x, 0):
					direcoes.append(Mover.ESQUERDA)
			if offset_y > 0:
				for i in range(0, offset_y):
					direcoes.append(Mover.FRENTE)

		elif self._ultima_dir == Mover.DIREITA:
			if offset_x > 0:
				for i in range(0, offset_y):
					direcoes.append(Mover.DIREITA)
			if offset_y > 0:
				for i in range(0, offset_y):
					direcoes.append(Mover.FRENTE)
			if offset_y < 0:
				for i in range(offset_y, 0):
					direcoes.append(Mover.TRAS)
			if offset_x < 0:
				for i in range(offset_x, 0):
					direcoes.append(Mover.ESQUERDA)

		elif self._ultima_dir == Mover.ESQUERDA:
			if offset_x < 0:
				for i in range(offset_y, 0):
					direcoes.append(Mover.ESQUERDA)
			if offset_y > 0:
				for i in range(0, offset_y):
					direcoes.append(Mover.FRENTE)
			if offset_y < 0:
				for i in range(offset_y, 0):
					direcoes.append(Mover.TRAS)
			if offset_x > 0:
				for i in range(0, offset_x):
					direcoes.append(Mover.DIREITA)

		else:
			if offset_y > 0:
				for i in range(0, offset_y):
					direcoes.append(Mover.FRENTE)
			if offset_x > 0:
				for i in range(0, offset_x):
					direcoes.append(Mover.DIREITA)
			if offset_x < 0:
				for i in range(offset_x, 0):
					direcoes.append(Mover.ESQUERDA)
			if offset_y < 0:
				for i in range(offset_y, 0):
					direcoes.append(Mover.TRAS)

		return direcoes


	def _verifica_pausa(self):
		global shared_obj
		if shared_obj.get(SharedObj.InterfacePauseContinua):
			print("[AUTOMATICO]: Pausa Setada")
			# Pausa setada, paramos e aguardamos algum evento ...
			self.historico_mov.append(Mover.PAUSA)
			while True:
				sleep(0.5)
				# Aguardamos duas coisas: continue ou fim do jogo
				if not shared_obj.get(SharedObj.InterfacePauseContinua):
					# Fim da pausa
					print("[AUTOMATICO]: Fim da pausa")
					self.historico_mov.append(Mover.CONTINUA)
					return Mover.CONTINUA

				if shared_obj.get(SharedObj.InterfaceFimJogo):
					# Fim do jogo
					print("[AUTOMATICO]: Fim do jogo")
					shared_obj.set(SharedObj.MoverMovimento, Mover.EXIT)
					return Mover.EXIT


	def _valida_caca(self):
		global shared_obj
		posicao = shared_obj.get(SharedObj.MoverCoordenada)
		msg = {'cmd': MsgSRtoSS.ValidaCaca, 'x': posicao[0], 'y': posicao[1]}

		shared_obj.clear_event(SharedObj.InterfaceRespValidaCacaEvent)
		self._envia_msg(msg)
		shared_obj.wait_event(SharedObj.InterfaceRespValidaCacaEvent)
		resp = shared_obj.get(SharedObj.InterfaceRespValidaCacaMsg)

		if 'ack' in resp:
			if resp['ack']:
				# Caca validada!
				self._x = posicao[0]
				self._y = posicao[1]
				self.cacas_encontradas.append(posicao)
				return (True, False)	# Retorna caca validada e posicao nao reajustada

			elif 'x' in resp and 'y' in resp:
				self._x = resp['x']
				self._y = resp['y']
				shared_obj.set(SharedObj.MoverCoordenada, (self._x, self._y))
				return (False, True)	# Retorna caca nao validada e posicao reajustada

		return (False, False)	# Caso de erro: nao conseguiu validar e nem ajustar posicao

	def _envia_msg(self, msg):
		global shared_obj
		shared_obj.set(SharedObj.TransmitirLock, msg)
		shared_obj.set_event(SharedObj.TransmitirEvent)

	def _informa_movimento_ss(self, x, y):
		global shared_obj
		print("[AUTOMATICO]: Informa movimento SS")
		msg = {'cmd': MsgSRtoSS.MovendoPara, 'x': x, 'y': y}
		self._envia_msg(msg)

	def _informa_posicao(self):
		global shared_obj
		print("[AUTOMATICO]: Informa posicao SS")
		posicao = shared_obj.get(SharedObj.MoverCoordenada)
		self._x = posicao[0]
		self._y = posicao[1]
		msg = {'cmd': MsgSRtoSS.PosicaoAtual, 'x': posicao[0], 'y': posicao[1]}
		self._envia_msg(msg)

	def atualiza_cacas(self):
		global shared_obj
		self.cacas_ordenadas = shared_obj.get(SharedObj.InterfaceCacasAtualizadas)
		shared_obj.set(SharedObj.InterfaceNovasCacas, 0)
		eu = (self._x, self._y)
		if eu in self.cacas_ordenadas:
			self.cacas_ordenadas.remove(eu)
			shared_obj.set(SharedObj.InterfaceCacasAtualizadas, self.cacas_ordenadas)

		self._ordena_cacas()
		print("[AUTOMATICO]: Novas cacas: %s" % str(self.cacas_ordenadas))

	def _finaliza_tudo(self):
		global shared_obj
		shared_obj.set(SharedObj.MoverMovimento, Mover.EXIT)
		shared_obj.set(SharedObj.InterfaceFimJogo, 1)
		pos_atual = (self._x, self._y)
		if pos_atual in self.cacas_encontradas:
			self.cacas_encontradas.remove(pos_atual)

		msg = {'cmd': MsgSRtoSS.FinalizaJogo}
		self._envia_msg(msg)


	def _go(self):
		global shared_obj
		if not len(self.cacas_ordenadas):
			return

		caca = self.cacas_ordenadas[0]
		print("[AUTOMATICO]: Proxima caca: %s" % str(caca))
		direcoes = self._calcula_direcoes(caca)
		print("[AUTOMATICO]: Direcoes : %s" % str(direcoes))
		while len(direcoes):
			direcao = direcoes.pop(0)
			# Limpa evento mover coordenada e seta direcao
			print("[AUTOMATICO]: Inicia movimento")
			shared_obj.clear_event(SharedObj.MoverCoordenadaEvent)
			mover_mov = shared_obj.get(SharedObj.MoverMovimento)
			if mover_mov == Mover.PARADO:
				shared_obj.set(SharedObj.MoverMovimento, direcao)

			# Espera calcular a proxima coordenada
			shared_obj.wait_event(SharedObj.MoverCoordenadaEvent)
			# Pega a coord
			prox_coord = shared_obj.get(SharedObj.MoverCoordenada)
			# Espera calcular a proxima coordenada
			shared_obj.clear_event(SharedObj.MoverCoordenadaEvent)
			# Envia ao SS a coordenada que o robo esta indo
			self._informa_movimento_ss(prox_coord[0], prox_coord[1])

			while True:
				end = shared_obj.get(SharedObj.MoverMovimento)
				if end == Mover.PARADO: break
				elif end == Mover.EXIT: return
				sleep(0.5)

			print("[AUTOMATICO]: Movimento finalizado")
			self.historico_mov.append(direcao)
			self._informa_posicao()

			if self._verifica_pausa() == Mover.EXIT:
				break
			if shared_obj.get(SharedObj.InterfaceFimJogo):
				break
			if shared_obj.get(SharedObj.InterfaceNovasCacas):
				break

	def run(self):
		global shared_obj
		print("[AUTOMATICO]: Iniciando buscas")
		# Primeira vez so ordena as cacas e sai cavando
		self._ordena_cacas()
		while True:
			if self._verifica_pausa() == Mover.EXIT:
				break

			self._go()
			if shared_obj.get(SharedObj.InterfaceFimJogo):
				break

			pos = shared_obj.get(SharedObj.MoverCoordenada)
			if pos in self.cacas_ordenadas:
				print("\n[AUTOMATICO]: Validando caca\n")
				ack, pos = self._valida_caca()
				if ack:
					print("\n[AUTOMATICO]: CACA VALIDADA!!\n")
				elif pos:
					print("\n[AUTOMATICO]: CACA INVALIDADA. POSICAO AJUSTADA\n")
				else:
					print("\n[AUTOMATICO]: CACA INVALIDADE E POSICAO NAO AJUSTADA. E AGORA?\nVAMOS ABORTAR !")
					# TODO: situacao de erro, pensar o que fazer
					break

			if not len(self.cacas_ordenadas):
				# FIM DO JOGO
				break

			self.atualiza_cacas()

		self._finaliza_tudo()
		print("[AUTOMATICO]: Finalizando ....")
		print("[AUTOMATICO]: Historico: %s" % str(self.historico_mov))
		print("[AUTOMATICO]: Cacas encontradas: %s" % str(self.cacas_encontradas))