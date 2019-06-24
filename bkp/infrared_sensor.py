#!/usr/bin/env python3
# so that script can be run from Brickman

from ev3dev.ev3 import *

# Connect infrared and touch sensors to any sensor ports
# and check they are connected.

ir = InfraredSensor() 
assert ir.connected, "Connect a single infrared sensor to any sensor port"

ir.mode = 'IR-PROX'

while True:    # Stop program by pressing touch sensor button
    # Infrared sensor in proximity mode will measure distance to the closest
    # object in front of it.
    distance = ir.value()

    if distance < 60:
        Leds.set_color(Leds.LEFT, Leds.RED)
    else:
        Leds.set_color(Leds.LEFT, Leds.GREEN)

Sound.beep()       
Leds.set_color(Leds.LEFT, Leds.GREEN)  
#make sure left led is green before exiting
