#!/usr/bin/env python3
from ev3dev.ev3 import *
from time import sleep, time

motor_direita = Motor(OUTPUT_C)
motor_esquerda = Motor(OUTPUT_B)
sensor_luminosidade = ColorSensor()
sensor_luminosidade.mode = 'COL-REFLECT'
max_ref = 0
min_ref = 100

motor_esquerda.run_timed(time_sp=2000, speed_sp=100)
end_time = time() + 2
while time() < end_time:
	read = sensor_luminosidade.value()
	if max_ref < read:
		max_ref = read
	if min_ref > read:
		min_ref = read
motor_esquerda.run_timed(time_sp=2000, speed_sp=-100)
print("max_ref %d min_ref %d" % (max_ref, min_ref))