import constant
import math
import pygame

class Car:
    pos_x = constant.STARTPOSX
    pos_y = constant.STARTPOSY
    speed = 0
    delta_speed = 0
    view_angle = 0
    delta_view_angle = 0
    name = ""
    activemalusfactor = 1
    carImage = pygame.image.load("car_2.png")


    def __init__(self, name, image):
        self.speed = 0
        self.view_angle = 0
        self.pos_x = constant.STARTPOSX
        self.pos_y = constant.STARTPOSY
        self.name = name
        self.carImage = pygame.image.load(image)
        self.delta_speed = 0
        self.delta_view_angle = 0
        self.activemalusfactor = 1
        pass

    def reset(self):
        self.speed = 0
        self.view_angle = 0
        self.pos_x = constant.STARTPOSX
        self.pos_y = constant.STARTPOSY
        pass

    def update(self):
        self.speed += self.delta_speed

        self.speedLimiter()

        self.view_angle += self.delta_view_angle

        self.pos_x += round(math.cos(
            math.radians(self.view_angle)) * self.speed)
        self.pos_y += round(math.sin(math.radians(self.view_angle)) * self.speed)
        pass


    def speedLimiter(self):



        if self.speed > constant.MAXSPEED * self.activemalusfactor:
            self.speed = constant.MAXSPEED * self.activemalusfactor
        if self.speed < (constant.MAXSPEED_REVERSE * -1 * self.activemalusfactor):
            self.speed = (constant.MAXSPEED_REVERSE * -1 * self.activemalusfactor)




    def accelerate(self):
        self.delta_speed += constant.ACCELERATIONVALUE
        pass

    def brake(self):
        self.delta_speed -= constant.ACCELERATIONVALUE
        pass

    def left(self):
        self.steering(-1); #steering mit passender Seite aufrufen -1 / 1 verändert nur dir richtung
        pass

    def right(self):
        self.steering(1) #steering mit passnder Seite aufrufen -1 / 1 verändert nur dir richtung
        pass

    def steering(self, side):
        self.delta_view_angle += constant.STEERINGVALUE * side
        pass


    def getPosAsRect(self):
        rect = pygame.Rect(self.pos_x, self.pos_y, constant.PLAYERHIGH, constant.PLAYERWITH)
        return rect

    def getimage(self):
        return pygame.transform.rotate(self.carImage, self.view_angle * -1) #Rotate winkel ist umgekehrt zu dem wie er in Game benutzt wird.


