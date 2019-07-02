from ev3dev.ev3 import *
from time import sleep

class Robo:
    SPEED = 200
    MOTOR_LEFT = "outB"
    MOTOR_RIGHT = 'outC'

    def __init__(self):
        
        self.modoDeJogo = 0  # mododeJogo igual a 0 para modo autonomo e 1 para modo manual
        self.velocidade = Robo.SPEED
        self.l = LargeMotor(Robo.MOTOR_LEFT)
        self.r = LargeMotor(Robo.MOTOR_RIGHT)
        self.cl = ColorSensor()
        self.colors = ('unknown', 'black', 'blue', 'green', 'yellow', 'red', 'white', 'brown')
        self.enviar = 0

    def frente(self):
        self.cl.mode = 'COL-COLOR'
        if self.colors[self.cl.value()] == "green" or self.colors[self.cl.value()] == "yellow" or self.colors[
            self.cl.value()] == "blue":
            while self.colors[self.cl.value()] == "green" or self.colors[self.cl.value()] == "yellow" or \
                    self.colors[
                        self.cl.value()] == "blue":
                self.r.run_forever(speed_sp=self.velocidade)
                self.l.run_forever(speed_sp=self.velocidade)
            else:
                self.stop()
        if self.colors[self.cl.value()] == "unknown":
            while self.colors[self.cl.value()] != "black":
                self.r.run_forever(speed_sp=self.velocidade)
        while self.colors[self.cl.value()] != "green":
            while self.colors[self.cl.value()] == "black":
                self.r.run_forever(speed_sp=self.velocidade / 2)
                self.l.run_forever(speed_sp=self.velocidade)
            while self.colors[self.cl.value()] == "white":
                self.r.run_forever(speed_sp=self.velocidade)
                self.l.run_forever(speed_sp=self.velocidade / 2)
            if self.colors[self.cl.value()] == "yellow":
                self.l.run_forever(speed_sp=self.velocidade)
                self.r.run_forever(speed_sp=self.velocidade)
                sleep(0.1)
                break
            if self.colors[self.cl.value()] == "blue":
                self.l.run_forever(speed_sp=self.velocidade)
                self.r.run_forever(speed_sp=self.velocidade)
                sleep(0.1)
                break
        else:
            self.l.run_forever(speed_sp=self.velocidade)
            self.r.run_forever(speed_sp=self.velocidade)
            sleep(0.1)
        self.stop()

    def esquerda(self):
        self.cl.mode = 'COL-COLOR'
        while self.colors[self.cl.value()] == "green":
            self.r.run_forever(speed_sp=self.velocidade)
            self.l.run_forever(speed_sp=self.velocidade * 0)
        else:
            self.l.stop(stop_action="hold")
        while self.colors[self.cl.value()] == "black":
            self.r.run_forever(speed_sp=self.velocidade)
        while self.colors[self.cl.value()] != "black":
            self.r.run_forever(speed_sp=self.velocidade)
        else:
            self.r.run_forever(speed_sp=self.velocidade)
        self.frente()

    def direita(self):
        self.cl.mode = 'COL-COLOR'
        while self.colors[self.cl.value()] == "green":
            self.l.run_forever(speed_sp=self.velocidade)
            self.r.run_forever(speed_sp=self.velocidade/2)
        else:
            self.r.stop(stop_action="hold")
        while self.colors[self.cl.value()] == "black":
            self.l.run_forever(speed_sp=self.velocidade)
        while self.colors[self.cl.value()] != "black":
            self.l.run_forever(speed_sp=self.velocidade)
        else:
            self.l.run_forever(speed_sp=self.velocidade)
        self.frente()

    def tras(self):
        self.cl.mode = 'COL-COLOR'
        while self.colors[self.cl.value()] == "green":
            self.l.run_forever(speed_sp=-self.velocidade)
        while self.colors[self.cl.value()] == "black":
            self.l.run_forever(speed_sp=-self.velocidade)
        while self.colors[self.cl.value()] != "black":
            self.l.run_forever(speed_sp=-self.velocidade)
        self.stop()
        self.frente()

    def stop(self):
        self.r.stop(stop_action="hold")
        self.l.stop(stop_action="hold")

  