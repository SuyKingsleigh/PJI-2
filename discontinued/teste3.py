from mover import Mover
from shared import SharedObj
from manual import Manual

global shared_obj
shared_obj = SharedObj()  # variavel global

# Jamal = Mover(0, 0)
Jamal = Manual([0, 0])
Jamal.start()

while True:
    user_input = input("> ")
    if user_input == "w":
        shared_obj.set(SharedObj.MoverMovimento, Mover.FRENTE)
        print("Andando para a frente")
    if user_input == "a":
        shared_obj.set(SharedObj.MoverMovimento, Mover.ESQUERDA)
        print('andando para esquerda')
    if user_input == "d":
        shared_obj.set(SharedObj.MoverMovimento, Mover.DIREITA)
        print('andando para a direita')
    if user_input == "s":
        shared_obj.set(SharedObj.MoverMovimento, Mover.TRAS)
        print('andando para tras')
    if user_input == "q":
        shared_obj.set(SharedObj.MoverMovimento, Mover.EXIT)


