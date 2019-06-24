#!/usr/bin/env python3
from ev3dev.ev3 import *
from time import sleep

# Connect EV3 color sensor and check connected.

cl = ColorSensor()
assert cl.connected, "Connect a color sensor to any sensor port"

# Put the color sensor into COL-REFLECT mode
# to measure reflected light intensity.
# In this mode the sensor will return a value between 0 and 100
cl.mode='COL-COLOR'

# 0=unknown, 1=black, 2=blue, 3=green, 4=yellow, 5=red, 6=white, 7=brown
while True:
	cor = cl.value()
	if cor == 1:
		print("preto %d" % cor)
	elif cor == 2:
		print("azul %d" % cor)
	elif cor == 3:
		print("verde %d" % cor)
	elif cor == 4:
		print("amarelo %d" % cor)
	elif cor == 5:
		print("vermelho %d" % cor)
	elif cor == 6:
		print("branco %d" % cor)
	elif cor == 7:
		print("marrom %d" % cor)
	else:
		print("indefinida %d" % cor)

	sleep(0.5)