from manual import Manual 

Jamal = Manual([0,0])

while True:
    user_input = input("> ")
    if user_input == "w": Jamal.move("frente")
    if user_input == "a": Jamal.move("esquerda")
    if user_input == "d": Jamal.move("direita")
    if user_input == "s": Jamal.move("tras")
    if user_input == "q": 
        Jamal.stop()
        break