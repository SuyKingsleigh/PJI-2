#!/usr/bin/env python3
from ev3dev.ev3 import *
import time

m_l = Motor(OUTPUT_B)#left motor
m_r = Motor(OUTPUT_C) #right motor

m_l.stop(stop_action='brake')
m_r.stop(stop_action='brake')

