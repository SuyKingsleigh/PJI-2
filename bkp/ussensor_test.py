#!/usr/bin/env python3
from ev3dev.ev3 import *
import time

m_l = Motor(OUTPUT_A)#left motor
m_r = Motor(OUTPUT_D) #right motor

us = UltrasonicSensor()
us.mode='US-DIST-CM'
units = us.units

distance = us.value()/10
print(str(distance) + " " + units)

while True:
    distance = us.value()/10
    print(str(distance) + " " + units)
    time.sleep(1)

