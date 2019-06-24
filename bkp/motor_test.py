#!/usr/bin/env python3
from ev3dev.ev3 import *
import time

m_l = Motor(OUTPUT_B)#left motor
m_r = Motor(OUTPUT_C) #right motor

#run forward for tree seconds:
m_l.run_timed(time_sp=3000, speed_sp=500)
m_r.run_timed(time_sp=3000, speed_sp=500)

time.sleep(2)

#run "forever"
for x in range(0,500):
	x=x+1
	m_l.run_forever(speed_sp=50)
	m_r.run_forever(speed_sp=50)
	if x ==500:
		m_l.stop(stop_action='brake')
		m_r.stop(stop_action='brake')

#turn back

m_l.run_timed(time_sp=3000, speed_sp=-500)
m_r.run_timed(time_sp=3000, speed_sp=-500)

time.sleep(2)

for y in range(0,500):
        y=y+1
        m_l.run_forever(speed_sp=-50)
        m_r.run_forever(speed_sp=-50)
        if y ==500:
                m_l.stop(stop_action='brake')
                m_r.stop(stop_action='brake')

#rotate

m_l.run_timed(time_sp=3000, speed_sp=500)
time.sleep(3)
m_r.run_timed(time_sp=3000, speed_sp=500)

