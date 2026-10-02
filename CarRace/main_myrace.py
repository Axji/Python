"""Autorennen mit pygame.

Steuerung: Pfeiltasten (Gas, Bremse, Lenken), Enter wechselt die Strecke, Escape beendet das Spiel.
Neben der Strasse wird das Auto langsamer. Die Strecken liegen als track_1.png, track_2.png, ... neben dem Skript.
"""
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
import ai
import neural_ai
import track_map

pygame.init()

# Farben (RGB)
bg = (255, 255, 255)
red = (255, 0, 0)
blue = (0, 0, 255)

# Fenster erstellen
fenster = pygame.display.set_mode((constant.WINDOWWITH, constant.WINDOWHIGH))
pygame.display.set_caption("NeuroSim")
fenster.fill(bg)

# Das Auto des Spielers; weitere Autos könnten in `playerlist` ergänzt werden
humanplayer = car.Car("Player", "car_2.png")
playerlist = [humanplayer]

# KI-Autos: jedes bekommt einen AIDriver, der es steuert (Parameter für unterschiedliches Fahrverhalten)
aidrivers = []
START_DELAY = 40  # Bilder Abstand, mit denen die KI-Autos nacheinander losfahren (alle starten am selben Punkt)
waiting = {}      # Auto -> noch zu wartende Bilder bis zum Start
# Name, Fahrstil und Farbe (der Spieler ist rot; Grün/Gelb/Grau sind Wiese, Ziellinie und Strasse)
for n, (ai_name, boldness, color) in enumerate([("AI vorsichtig", 0.8, (0, 110, 255)),
                                                ("AI mutig", 1.0, (180, 60, 230)),
                                                ("AI normal", 0.9, (0, 220, 220))], start=1):
    ai_car = car.Car(ai_name, "car_1.png", color)
    playerlist.append(ai_car)
    aidrivers.append(ai.AIDriver(ai_car, boldness=boldness, obstacles=playerlist))
    waiting[ai_car] = n * START_DELAY

# Lernende KI: fährt mit dem gespeicherten Netz (brains/best_brain.json, erzeugt mit train_neural.py), falls vorhanden
neural_driver = None
brain, _ = neural_ai.load_brain()
if brain:
    neural_car = car.Car("AI lernend", "car_1.png", (255, 130, 200))
    neural_car.is_neural = True
    playerlist.append(neural_car)
    neural_driver = neural_ai.NeuralDriver(neural_car, brain)
    waiting[neural_car] = (len(aidrivers) + 1) * START_DELAY
track_maps = {}   # Streckennummer -> TrackMap (wird erst gebraucht, wenn die lernende KI fährt)

explosions = []   # [x, y, verbleibende Bilder] der sichtbaren Zusammenstösse

# Alle vorhandenen Strecken track_1.png, track_2.png, ... laden
tracks = []
track_id = 1
while os.path.exists(f"track_{track_id}.png"):
    tracks.append(pygame.image.load(f"track_{track_id}.png"))
    track_id += 1

activeTrackNumber = 0  # Index der aktuell gefahrenen Strecke

player_1 = pygame.Rect(100, 165, 20, 20)
image_1 = pygame.image.load("car_1.png")

explosion = pygame.image.load("explosion.png")

# Bildrate begrenzen
clock = pygame.time.Clock()
fps = 30
time_ = 0


def getmalus(pos_x, pos_y):
    """Liefert den Tempo-Faktor für die Position: 1 auf der Strasse, sonst MALUSFACTOR (Abseits)."""
    # Geprüft wird der Pixel in der Mitte des Autos (Position + halbe Autogrösse)
    x = int(pos_x) + 10
    y = int(pos_y) + 10
    # Ausserhalb des Fensters gilt als Abseits (get_at() würde sonst IndexError werfen)
    if not (0 <= x < fenster.get_width() and 0 <= y < fenster.get_height()):
        return constant.MALUSFACTOR
    if fenster.get_at((x, y)) != constant.COLOR_STREET:
        return constant.MALUSFACTOR
    return 1


# Hauptschleife des Spiels
running = True
while running:
    # Tastatur- und Fensterereignisse verarbeiten
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

            # Enter: nächste Strecke laden (nach der letzten wieder die erste) und Autos zurücksetzen
            if event.key == K_RETURN:
                activeTrackNumber += 1
                if activeTrackNumber >= len(tracks):
                    activeTrackNumber = 0

                for player in playerlist:
                    player.reset()
                for n, driver in enumerate(aidrivers, start=1):
                    waiting[driver.car] = n * START_DELAY
                if neural_driver:
                    waiting[neural_driver.car] = (len(aidrivers) + 1) * START_DELAY
                explosions.clear()

            # Taste gedrückt: Gas, Bremse bzw. Lenkung einschalten
            if event.key == K_UP:
                humanplayer.accelerate()
            if event.key == K_LEFT:
                humanplayer.left()
            if event.key == K_RIGHT:
                humanplayer.right()
            if event.key == K_DOWN:
                humanplayer.brake()

        # Taste losgelassen: Wirkung wieder aufheben (Gegenbewegung)
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

    # KI-Fahrer entscheiden anhand der Strecke, bevor die Autos bewegt werden
    for driver in aidrivers:
        if waiting[driver.car] == 0:
            driver.drive(tracks[activeTrackNumber])

    if neural_driver and waiting[neural_driver.car] == 0:
        if activeTrackNumber not in track_maps:
            track_maps[activeTrackNumber] = track_map.TrackMap(tracks[activeTrackNumber])
        neural_driver.drive(track_maps[activeTrackNumber])

    # Alle Player updaten. Die Strecke muss angezeigt werden, damit je nach Boden ein Malus berechnet wird.
    # Noch wartende KI-Autos stehen am Start (ohne Kollision, damit sie nicht festkleben).
    car.update_catchup([p for p in playerlist if waiting.get(p, 0) == 0 and not p.is_neural], fps)
    for player in playerlist:
        if waiting.get(player, 0) > 0:
            waiting[player] -= 1
            continue
        player.setmalus(getmalus(player.pos_x, player.pos_y))
        player.update()

    # Zusammenstösse zwischen allen Autopaaren erkennen
    active = [p for p in playerlist if waiting.get(p, 0) == 0]
    for i, first in enumerate(active):
        for second in active[i + 1:]:
            # Die lernende KI kollidiert nicht mit anderen KI-Autos, nur mit dem Spieler
            if (first.is_neural or second.is_neural) and humanplayer not in (first, second):
                continue
            hit = car.resolve_collision(first, second)
            if hit:
                explosions.append([hit[0], hit[1], 10])

    for player in playerlist:
        fenster.blit(player.getimage(), player.getPosAsRect())

    # Explosionsbild kurz am Kollisionspunkt anzeigen
    for boom in explosions:
        fenster.blit(explosion, explosion.get_rect(center=(boom[0], boom[1])))
        boom[2] -= 1
    explosions[:] = [b for b in explosions if b[2] > 0]

    pygame.display.update()

    clock.tick(fps)

pygame.quit()
sys.exit()
