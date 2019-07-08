# v.8.14.17
from time import sleep

from ev3dev.ev3 import *

class Mover:
	"""docstring for Mover"""
	EXIT = -1
	PARADO = 0
	FRENTE = 1
	DIREITA = 2
	TRAS = 3
	ESQUERDA = 4

	PAUSA = 10
	CONTINUA = 11

class Robo:
    SPEED = 200
    MOTOR_LEFT = "outB"
    MOTOR_RIGHT = 'outC'

    def __init__(self):

        self.speed = Robo.SPEED
        self.left_motor = LargeMotor(Robo.MOTOR_LEFT)
        self.right_motor = LargeMotor(Robo.MOTOR_RIGHT)
        self.colour_sensor = ColorSensor()
        self.colours = ('unknown', 'black', 'blue', 'green', 'yellow', 'red', 'white', 'brown')

    def frente(self):
        self.colour_sensor.mode = 'COL-COLOR'
        if self.colours[self.colour_sensor.value()] == "green" or self.colours[
            self.colour_sensor.value()] == "yellow" or self.colours[
            self.colour_sensor.value()] == "blue":
            while self.colours[self.colour_sensor.value()] == "green" or self.colours[
                self.colour_sensor.value()] == "yellow" or \
                    self.colours[
                        self.colour_sensor.value()] == "blue":
                self.right_motor.run_forever(speed_sp=self.speed)
                self.left_motor.run_forever(speed_sp=self.speed)
            else:
                self._stop()

        if self.colours[self.colour_sensor.value()] == "unknown":
            while self.colours[self.colour_sensor.value()] != "black":
                self.right_motor.run_forever(speed_sp=self.speed)
        while self.colours[self.colour_sensor.value()] != "green":
            while self.colours[self.colour_sensor.value()] == "black":
                self.right_motor.run_forever(speed_sp=self.speed / 2)
                self.left_motor.run_forever(speed_sp=self.speed)
            while self.colours[self.colour_sensor.value()] == "white":
                self.right_motor.run_forever(speed_sp=self.speed)
                self.left_motor.run_forever(speed_sp=self.speed / 2)
            if self.colours[self.colour_sensor.value()] == "yellow":
                self.left_motor.run_forever(speed_sp=self.speed)
                self.right_motor.run_forever(speed_sp=self.speed)
                sleep(0.1)
                break
            if self.colours[self.colour_sensor.value()] == "blue":
                self.left_motor.run_forever(speed_sp=self.speed)
                self.right_motor.run_forever(speed_sp=self.speed)
                sleep(0.1)
                break
        else:
            self.left_motor.run_forever(speed_sp=self.speed)
            self.right_motor.run_forever(speed_sp=self.speed)
            sleep(0.1)
        self._stop()

    def esquerda(self):
        self.colour_sensor.mode = 'COL-COLOR'
        while self.colours[self.colour_sensor.value()] == "green":
            self.right_motor.run_forever(speed_sp=self.speed)
            self.left_motor.run_forever(speed_sp=self.speed * 0)
        else:
            self.left_motor.stop(stop_action="hold")
        while self.colours[self.colour_sensor.value()] == "black":
            self.right_motor.run_forever(speed_sp=self.speed)
        while self.colours[self.colour_sensor.value()] != "black":
            self.right_motor.run_forever(speed_sp=self.speed)
        else:
            self.right_motor.run_forever(speed_sp=self.speed)
        self.frente()

    def direita(self):
        self.colour_sensor.mode = 'COL-COLOR'
        while self.colours[self.colour_sensor.value()] == "green":
            self.left_motor.run_forever(speed_sp=self.speed)
            self.right_motor.run_forever(speed_sp=self.speed / 2)
        else:
            self.right_motor.stop(stop_action="hold")
        while self.colours[self.colour_sensor.value()] == "black":
            self.left_motor.run_forever(speed_sp=self.speed)
        while self.colours[self.colour_sensor.value()] != "black":
            self.left_motor.run_forever(speed_sp=self.speed)
        else:
            self.left_motor.run_forever(speed_sp=self.speed)
        self.frente()

    def tras(self):
        self.colour_sensor.mode = 'COL-COLOR'
        while self.colours[self.colour_sensor.value()] == "green":
            self.left_motor.run_forever(speed_sp=-self.speed)
        while self.colours[self.colour_sensor.value()] == "black":
            self.left_motor.run_forever(speed_sp=-self.speed)
        while self.colours[self.colour_sensor.value()] != "black":
            self.left_motor.run_forever(speed_sp=-self.speed)
        self._stop()
        self.frente()

    def _stop(self):
        self.right_motor.stop(stop_action="hold")
        self.left_motor.stop(stop_action="hold")
