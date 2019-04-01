#!/usr/bin/env python3

from ev3dev.ev3 import * 
from time import sleep

mB = LargeMotor('outB')
mC = LargeMotor('outC')

def forward():
    mB.run_timed(speed_sp=500, time_sp=1000)
    mC.run_timed(speed_sp=500, time_sp=1000)
    sleep(1)

def right():
    mB.run_timed(speed_sp=800, time_sp=400)
    sleep(1)

def left():
    mC.run_timed(speed_sp=800, time_sp=400)
    sleep(1)
def backwards():
    mC.run_timed(speed_sp=-500, time_sp=1000)
    mB.run_timed(speed_sp=-500, time_sp=1000)
    sleep(1)

while(True):
	inp = str(input(">  "))
	if(inp=="q"): break
	if(inp=="w"): forward()
	if(inp=="a"): left()
	if(inp=="s"): backwards()
	if(inp=="d"): right()
