from threading import Thread
from time import time, sleep

from ev3dev.ev3 import *
from shared import *


class Cor(object):
	# 0=unknown, 1=black, 2=blue, 3=green, 4=yellow, 5=red, 6=white, 7=brown
	INDEFINIDO = 0
	PRETO = 1
	AZUL = 2
	VERDE = 3
	AMARELO = 4
	VERMELHO = 5
	BRANCO = 6
	MARROM = 7

	corToString = {
		INDEFINIDO: 'indefinido',
		PRETO: 'preto',
		AZUL: 'azul',
		VERDE: 'verde',
		AMARELO: 'amarelo',
		VERMELHO: 'vermelho',
		BRANCO: 'branco',
		MARROM: 'marrom'
	}


class Mover(Thread):
	"""docstring for Mover"""
	EXIT = -1
	PARADO = 0
	FRENTE = 1
	DIREITA = 2
	TRAS = 3
	ESQUERDA = 4

	PAUSA = 10
	CONTINUA = 11

	def __init__(self, x, y):
		self.motor_direita = Motor(OUTPUT_C)
		self.motor_esquerda = Motor(OUTPUT_B)
		self.sensor_us = UltrasonicSensor()
		self.sensor_luminosidade = ColorSensor()

		# Configura modo dos sensores
		self.sensor_luminosidade.mode = 'COL-REFLECT'
		self.sensor_us.mode = 'US-DIST-CM'
        # assert colour_sensor.connected, "Connect a color sensor to any sensor port"

		# Atributos ocultos
		self._ultima_direcao = Mover.FRENTE
		self._min_ref = 5
		self._max_ref = 80
		self._coord_ini = (x, y)
		self._coord_x = x
		self._coord_y = y
		self._next_coord = (x, y)

		shared_obj.clear_event(SharedObj.MoverCoordenadaEvent)
		shared_obj.set(SharedObj.MoverCoordenada, self._coord_ini)

		super(Mover, self).__init__()


	def calibra_girando(self):
		"""Calibra fazendo meia volta e retornando a posicao original"""
		speed = 150
		for i in range(0, 2):
			self.motor_direita.run_forever(speed_sp=speed)
			end_time = time() + 2
			while time() < end_time:
				read = self.sensor_luminosidade.value()
				if self._max_ref < read:
					self._max_ref = read
				if self._min_ref > read:
					self._min_ref = read
			self.motor_direita.stop()
			speed -= 290


	def calibra_andando(self):
		"""Calibra ja andando pra frente"""
		self.sensor_luminosidade.mode = 'COL-REFLECT'
		self.motor_esquerda.run_direct(duty_cycle_sp=30)
		self.motor_direita.run_direct(duty_cycle_sp=30)
		self._max_ref = 0
		self._min_ref = 100
		end_time = time() + 5
		while time() < end_time:
			read = self.sensor_luminosidade.value()
			if self._max_ref < read:
				self._max_ref = read
			if self._min_ref > read:
				self._min_ref = read


	def _encontra_faixa(self, encontra_faixa_esquerda=False):
		self.sensor_luminosidade.mode = 'COL-COLOR'

		if self.sensor_luminosidade.value() == Cor.PRETO:
			return

		vel = 100
		if encontra_faixa_esquerda:
			self.motor_esquerda.run_timed(time_sp=500, speed_sp=vel)
			end_time = time() + 0.5
			while time() < end_time:
				if self.sensor_luminosidade.value() == Cor.PRETO:
					self.stop()
					return

			self.stop()
			self.motor_esquerda.run_timed(time_sp=500, speed_sp=-vel)
			self.motor_direita.run_timed(time_sp=500, speed_sp=2*vel)
			end_time = time() + 0.5
			while time() < end_time:
				if self.sensor_luminosidade.value() == Cor.PRETO:
					sleep(0.2)
					self.stop()
					return
		else:
			self.motor_direita.run_timed(time_sp=500, speed_sp=vel)
			end_time = time() + 0.5
			while time() < end_time:
				if self.sensor_luminosidade.value() == Cor.PRETO:
					self.stop()
					return

			self.stop()
			self.motor_direita.run_timed(time_sp=500, speed_sp=-vel)
			self.motor_esquerda.run_timed(time_sp=500, speed_sp=2*vel)
			end_time = time() + 0.5
			while time() < end_time:
				if self.sensor_luminosidade.value() == Cor.PRETO:
					sleep(0.2)
					self.stop()
					return


	def _calc_next_coord(self, direcao):
		global shared_obj
		shared_obj.clear_event(SharedObj.MoverCoordenadaEvent)
		coord = shared_obj.get(SharedObj.MoverCoordenada)
		coord_x = coord[0]
		coord_y = coord[1]

		if self._coord_ini == (0, 0):
			if direcao == Mover.FRENTE:
				coord_y += 1
			elif direcao == Mover.DIREITA:
				coord_x += 1
			elif direcao == Mover.TRAS:
				coord_y -= 1
			elif direcao == Mover.ESQUERDA:
				coord_x -= 1

		elif self._coord_ini == (6, 6):
			if direcao == Mover.FRENTE:
				coord_y -= 1
			elif direcao == Mover.DIREITA:
				coord_x -= 1
			elif direcao == Mover.TRAS:
				coord_y += 1
			elif direcao == Mover.ESQUERDA:
				coord_x += 1

		shared_obj.set_event(SharedObj.MoverCoordenadaEvent)
		return (coord_x, coord_y)


	def _verifica_pausa(self):
		global shared_obj
		if shared_obj.get(SharedObj.MoverMovimento) == Mover.PAUSA:
			print("EM PAUSA !! Aguardando algo ...")
			self.stop()
			shared_obj.append_list(SharedObj.MoverHistorico, Mover.PAUSA)
            # self._stop()
			while True:
				sleep(0.5)

				if shared_obj.get(SharedObj.MoverMovimento) == Mover.CONTINUA \
				or shared_obj.get(SharedObj.MoverMovimento) == Mover.PARADO:
					shared_obj.append_list(SharedObj.MoverHistorico, Mover.CONTINUA)
					break

				if shared_obj.get(SharedObj.MoverMovimento) == Mover.EXIT:
					return Mover.EXIT

		return Mover.CONTINUA


	def _finalizar_movimento(self):
		global shared_obj
		self.stop()
		shared_obj.acquire(SharedObj.MoverMovimento)
		if shared_obj.get_directly(SharedObj.MoverMovimento) != Mover.EXIT:
			shared_obj.set_directly(SharedObj.MoverMovimento, Mover.PARADO)
		shared_obj.release(SharedObj.MoverMovimento)


	def move(self, direcao):
		global shared_obj
		"""Move em uma direcao (frente, direita, esquerda, tras).
			Se for passada a mesma direcao, calibra e segue em fente"""

		if direcao == Mover.PARADO or direcao == Mover.EXIT:
			self.stop()
			return

		if self._verifica_pausa() == Mover.EXIT:
			return

		calc_coord = self._calc_next_coord(direcao)
		self._next_coord = calc_coord
		shared_obj.set(SharedObj.MoverCoordenada, calc_coord)

		if direcao != self._ultima_direcao:
			if (direcao == Mover.FRENTE and self._ultima_direcao == Mover.TRAS) or \
				(direcao == Mover.TRAS and self._ultima_direcao == Mover.FRENTE) or \
				(direcao == Mover.DIREITA and self._ultima_direcao == Mover.ESQUERDA) or \
				(direcao == Mover.ESQUERDA and self._ultima_direcao == Mover.DIREITA):
				self._go_back()
			elif not (self._coord_x == 6 and self._coord_y == 6): 
				self._go_front()
			faixa_esq = self._gira(direcao)
			self._encontra_faixa(faixa_esq)
			self._ultima_direcao = direcao
		else:
			self._go_front()
			self._encontra_faixa()

		# self.calibra_andando()
		# power, target, kp, kd, ki, direction, minref, maxref
		target = (self._min_ref + self._max_ref)/2
		self._anda(50, target, float(0.65), 1, float(0.02), 1, self._min_ref, self._max_ref)
		self._coord_x = calc_coord[0]
		self._coord_y = calc_coord[1]
		self._finalizar_movimento()

		#Salvar os movimentos no historico
		if direcao != Mover.PARADO and direcao != Mover.EXIT:
			shared_obj.append_list(SharedObj.MoverHistorico, direcao)


	def stop(self):
		"""Para os dois motores"""
		self.motor_esquerda.stop(stop_action='brake')
		self.motor_direita.stop(stop_action='brake')


	def _go_front(self):
		self.sensor_luminosidade.mode = 'COL-COLOR'
		cor = self.sensor_luminosidade.value()
		self.motor_esquerda.run_forever(speed_sp=100)
		self.motor_direita.run_forever(speed_sp=100)
		while True:
			if self.sensor_luminosidade.value() != cor:
				sleep(0.5)
				self.stop()
				break;


	def _go_back(self):
		self.sensor_luminosidade.mode = 'COL-COLOR'
		cor = self.sensor_luminosidade.value()
		self.motor_esquerda.run_forever(speed_sp=-100)
		self.motor_direita.run_forever(speed_sp=-100)
		while True:
			if self.sensor_luminosidade.value() != cor:
				sleep(0.5)
				self.stop()
				break;


	def _gira(self, direcao):
		"""Gira 90, -90, 180 ou 270 graus"""
		self.sensor_luminosidade.mode = 'COL-REFLECT'
		esquerda = False
		encontra_faixa_esquerda = False

		if direcao == self._ultima_direcao:
			return

		if direcao == Mover.FRENTE:
			if self._ultima_direcao == Mover.ESQUERDA:
				self.motor_esquerda.run_forever(speed_sp=100)
			elif self._ultima_direcao == Mover.DIREITA:
				# self.motor_direita.run_forever(speed_sp=25)
				self.motor_esquerda.run_forever(speed_sp=-100)
				encontra_faixa_esquerda  = True
			elif self._ultima_direcao == Mover.TRAS:
				self._gira(Mover.ESQUERDA)
				return False

		elif direcao == Mover.DIREITA:
			if self._ultima_direcao == Mover.FRENTE:
				self.motor_esquerda.run_forever(speed_sp=100)
			elif self._ultima_direcao == Mover.TRAS:
				# self.motor_direita.run_forever(speed_sp=25)
				self.motor_esquerda.run_forever(speed_sp=-100)
				encontra_faixa_esquerda = True
			elif self._ultima_direcao == Mover.ESQUERDA:
				self._gira(Mover.FRENTE)
				return False

		elif direcao == Mover.ESQUERDA:
			if self._ultima_direcao == Mover.FRENTE:
				# self.motor_direita.run_forever(speed_sp=25)
				self.motor_esquerda.run_forever(speed_sp=-100)
				encontra_faixa_esquerda = True
			elif self._ultima_direcao == Mover.TRAS:
				self.motor_esquerda.run_forever(speed_sp=100)
			elif self._ultima_direcao == Mover.DIREITA:
				self._gira(Mover.TRAS)
				return False

		elif direcao == Mover.TRAS:
			if self._ultima_direcao == Mover.DIREITA:
				self.motor_esquerda.run_forever(speed_sp=100)
			elif self._ultima_direcao == Mover.ESQUERDA:
				# self.motor_direita.run_forever(speed_sp=25)
				self.motor_esquerda.run_forever(speed_sp=-100)
				encontra_faixa_esquerda = True
			elif self._ultima_direcao == Mover.FRENTE:
				self._gira(Mover.DIREITA)
				return False

		else:
			return encontra_faixa_esquerda

		sleep(1)
		while True:
			luminosidade = self.sensor_luminosidade.value()
			# if luminosidade != Cor.PRETO:
			# 	break

			if luminosidade <= (self._min_ref+5):
				if esquerda:
					esquerda = False
					sleep(0.5)
					continue
				sleep(0.4)
				self.stop()
				break;
		return encontra_faixa_esquerda


	def _steering(self, course, power):
		power_left = power_right = power
		s = (50 - abs(float(course))) / 50
		if course >= 0:
			power_right *= s
			if course > 100:
				power_right = - power
		else:
			power_left *= s
			if course < -100:
				power_left = - power
		return (int(power_left), int(power_right))


	def _anda(self, power, target, kp, kd, ki, direction, minRef, maxRef):
		global shared_obj
		lastError = error = integral = 0
		self.motor_esquerda.run_direct()
		self.motor_direita.run_direct()
		while True:
			if self._verifica_pausa() == Mover.EXIT:
				return
			else:
				self.motor_esquerda.run_direct()
				self.motor_direita.run_direct()

			mov = shared_obj.get(SharedObj.MoverMovimento)
			if mov == Mover.PARADO or mov == Mover.EXIT:
				self.stop()
				break

			self.sensor_luminosidade.mode='COL-REFLECT'
			if self._next_coord == (6, 6):
				if int(lastError) < -30:
					self.stop()
					break

			if (self.sensor_us.value()/10) < 10:
				print("Obstaculo encontrado")
				self.stop()
				break

			refRead = self.sensor_luminosidade.value()
			error = target - (100 * ( refRead - minRef ) / ( maxRef - minRef ))
			derivative = error - lastError
			lastError = error
			integral = float(0.5) * integral + error
			course = (kp * error + kd * derivative +ki * integral) * direction
			for (motor, pow) in zip((self.motor_esquerda, self.motor_direita), self._steering(course, power)):
				motor.duty_cycle_sp = pow
			sleep(0.01) # Aprox 100Hz

			# Verifica cor
			self.sensor_luminosidade.mode='COL-COLOR'
			cor = self.sensor_luminosidade.value()
			if (cor != Cor.PRETO) and (cor != Cor.BRANCO):
				self.stop()
				break;


	def run(self):
		global shared_obj
		while True:
			if self._verifica_pausa() == Mover.EXIT:
				break

			move = shared_obj.get(SharedObj.MoverMovimento)
			if move != Mover.PARADO:
					self.move(move)

			if move == Mover.EXIT:
				break

			sleep(0.1)

