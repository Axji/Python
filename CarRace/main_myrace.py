# debugged: angle, explosion
import os
import sys

# Bilder und Module werden relativ zu diesem Ordner geladen, egal von wo das Spiel gestartet wird.
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pygame
from pygame.locals import *

import constant
import car

pygame.init()

bg = (255, 255, 255)
red = (255, 0, 0)
blue = (0, 0, 255)

fenster = pygame.display.set_mode((constant.WINDOWWITH, constant.WINDOWHIGH))
pygame.display.set_caption("NeuroSim")
fenster.fill(bg)

humanplayer = car.Car("Player", "car_2.png")
playerlist = [humanplayer]

# Alle vorhandenen Strecken track_1.png, track_2.png, ... laden
tracks = []
track_id = 1
while os.path.exists(f"track_{track_id}.png"):
    tracks.append(pygame.image.load(f"track_{track_id}.png"))
    track_id += 1

activeTrackNumber = 0

player_1 = pygame.Rect(100, 165, 20, 20)
image_1 = pygame.image.load("car_1.png")

explosion = pygame.image.load("explosion.png")

clock = pygame.time.Clock()
fps = 30
time_ = 0


def getmalus(pos_x, pos_y):
    x = int(pos_x) + 10
    y = int(pos_y) + 10
    # Ausserhalb des Fensters gilt als Abseits (get_at() würde sonst IndexError werfen)
    if not (0 <= x < fenster.get_width() and 0 <= y < fenster.get_height()):
        return constant.MALUSFACTOR
    if fenster.get_at((x, y)) != constant.COLOR_STREET:
        return constant.MALUSFACTOR
    return 1


running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

            if event.key == K_RETURN:
                activeTrackNumber += 1
                if activeTrackNumber >= len(tracks):
                    activeTrackNumber = 0

                for player in playerlist:
                    player.reset()

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

    # Rennstrecke rendern
    fenster.blit(tracks[activeTrackNumber], (0, 0))

    # Alle Player updaten. Die Strecke muss angezeigt werden, damit je nach Boden ein Malus berechnet wird.
    for player in playerlist:
        player.setmalus(getmalus(player.pos_x, player.pos_y))
        player.update()
        fenster.blit(player.getimage(), player.getPosAsRect())

    pygame.display.update()

    clock.tick(fps)

pygame.quit()
sys.exit()
