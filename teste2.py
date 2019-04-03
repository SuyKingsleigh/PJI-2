from mover import Mover 
from manual import  Manual


# Testar os dois
Jamal = Mover(0,0)
# Jamal = Manual([0,0])

# Loop para mover o robo 
while True:
    user_input = input("> ")
    if user_input == "w": Jamal.move(Mover.FRENTE)
    if user_input == "a": Jamal.move(Mover.ESQUERDA)
    if user_input == "d": Jamal.move(Mover.DIREITA)
    if user_input == "s": Jamal.move(Mover.TRAS)
    if user_input == "q":
        Jamal.move(Mover.EXIT)
        break

