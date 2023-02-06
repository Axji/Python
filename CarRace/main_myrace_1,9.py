# debugged: angle, explosion
import pygame, sys, math, time
import constant
import car
from pygame.locals import *

pygame.init()

bg = (255, 255, 255)
red = (255, 0, 0)
blue = (0, 0, 255)

fenster = pygame.display.set_mode((constant.WINDOWWITH, constant.WINDOWHIGH))
pygame.display.set_caption("NeuroSim")
fenster.fill(bg)

humanplayer = car.Car("Player", "car_2.png")
playerlist = []

playerlist.append(humanplayer)

tracks = []
trackfilefound = 1

trackID = 1
while trackfilefound == 1:
    try:
        exec("tracks.append(pygame.image.load('track_" + str(trackID) + ".png'))")
    except:
        trackfilefound = 0
    trackID += 1

activeTrackNumber = 0

player_1 = pygame.Rect(100, 165, 20, 20)
image_1 = pygame.image.load("car_1.png")

explosion = pygame.image.load("explosion.png")

clock = pygame.time.Clock()
fps = 30
time_ = 0


def getmalus(pos_x, pos_y):
    if not fenster.get_at((player_1.left + 10, player_1.top + 10)) == constant.COLOR_STREET:
        return constant.MALUSFACTOR
    pass


while True:
    for event in pygame.event.get():

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit();

            if event.key == K_RETURN:

                activeTrackNumber += 1
                if activeTrackNumber >= len(tracks):
                    activeTrackNumber = 0

                for car.Car in playerlist:
                    car.reset()


            if event.key == K_UP:
                humanplayer.accelerate()
            if event.key == K_LEFT:
                humanplayer.left()
            if event.key == K_RIGHT:
                humanplayer.right()
            if event.key == K_DOWN:
                humanplayer.brake()

        if event.type == KEYUP:
            if event.key == K_UP:
                humanplayer.brake()
            if event.key == K_LEFT:
                humanplayer.right()
            if event.key == K_RIGHT:
                humanplayer.left()
            if event.key == K_DOWN:
                humanplayer.accelerate()

    #rennstrecke rendern
    fenster.blit(tracks[activeTrackNumber], (0, 0))

    #alle player updaten wichtig die Strecke mnuss angezeigt werden das je nach Boden ein Malus berechnet wird.
    for car in playerlist:
        car.setmalus(getmalus(car.pos_x, car.pos_y))
        car.update()
        fenster.blit(car.getimage(), car.getPosAsRect())

    pygame.display.update()

    # time_ += 1
    clock.tick(fps)

pygame.quit()
#
