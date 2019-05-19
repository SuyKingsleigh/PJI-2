# from mover_test import *
from mover import *
from interface import *
from threading import Thread, Lock
from time import sleep
from shared import *
from mensagens_robo import *


class Manual(Thread):
	def __init__(self, coord):
		self.posicao_inicial = coord
		self.historico_mov = []
		self._x = coord[0]
		self._y = coord[1]
		self._ultima_dir = Mover.FRENTE

		self.movedor = Mover(self._x, self._y)
		self.movedor.start()

		super(Manual, self).__init__()


	def _verifica_pausa(self):
		global shared_obj
		if shared_obj.get(SharedObj.InterfacePauseContinua) == 1:
			print("[MANUAL]: Entrou em pausa")

			# Pausa setada, paramos e aguardamos algum evento ...
			while True:
				sleep(0.5)
				# Aguardamos duas coisas: continue ou fim do jogo
				if not shared_obj.get(SharedObj.InterfacePauseContinua):
					# Fim da pausa
					print("[MANUAL]: Fim da pausa")
					return Mover.CONTINUA

				if shared_obj.get(SharedObj.InterfaceFimJogo):
					# Fim do jogo
					print("[MANUAL]: Fim do jogo")
					shared_obj.set(SharedObj.MoverMovimento, Mover.EXIT)
					return Mover.EXIT

		else:
			return shared_obj.get(SharedObj.ManualMovimento)


	def _avisa_posicao_atual(self):
		global shared_obj
		print("[MANUAL]: Informa posicao SS")
		coord = shared_obj.get(SharedObj.MoverCoordenada)
		msg = {'cmd': MsgSRtoSS.PosicaoAtual, 'x': coord[0], 'y': coord[1]}
		shared_obj.set(SharedObj.TransmitirLock, msg)
		shared_obj.set_event(SharedObj.TransmitirEvent)

	def _avisa_movimento(self, x, y):
		global shared_obj
		print("[MANUAL]: Informa movimento SS")
		msg = {'cmd': MsgSRtoSS.MovendoPara, 'x': x, 'y': y}
		shared_obj.set(SharedObj.TransmitirLock, msg)
		shared_obj.set_event(SharedObj.TransmitirEvent)

	def move(self, direcao):
		global shared_obj

		print("[MANUAL]: Movendo para %s" % str(direcao))
		# Limpa evento mover coordenada
		shared_obj.clear_event(SharedObj.MoverCoordenadaEvent)
		# Seta direcao para a thread movimento
		shared_obj.set(SharedObj.MoverMovimento, direcao)
		# Espera calcular a proxima coordenada
		shared_obj.wait_event(SharedObj.MoverCoordenadaEvent)
		# Pega proxima coord
		prox_coord = shared_obj.get(SharedObj.MoverCoordenada)
		print('prox coord: ' + prox_coord)
		# Limpa evento mover coordenada
		shared_obj.clear_event(SharedObj.MoverCoordenadaEvent)
		# Envia ao SS a coordenada que o robo esta indo
		self._avisa_movimento(prox_coord[0], prox_coord[1])

		while True:
			# Mutex manual vem da interface
			mut_manual = shared_obj.get(SharedObj.ManualMovimento)
			if mut_manual == Mover.EXIT:
				shared_obj.set(SharedObj.MoverMovimento, Mover.EXIT)

			# Mutex movimento e do mover (aguarda finalizar o movimento)
			if shared_obj.get(SharedObj.MoverMovimento) == Mover.PARADO:
				print("[MANUAL]: Movimento finalizado")
				break

			sleep(0.1)

		self._avisa_posicao_atual()
		if shared_obj.get(SharedObj.ManualMovimento) != Mover.EXIT:
			shared_obj.set(SharedObj.ManualMovimento, Mover.PARADO)


	def run(self):
		global shared_obj
		print("[MANUAL]: Aguardando movimentos")
		while True:
			pausa = self._verifica_pausa()
			if pausa == Mover.EXIT:
				break

			mov = shared_obj.get(SharedObj.ManualMovimento)
			if mov != Mover.PARADO:
				if mov == Mover.EXIT:
					shared_obj.set(SharedObj.MoverMovimento, Mover.EXIT)
					break

				self.move(mov)

			sleep(1)

		print("[MANUAL]: Fim do jogo")

