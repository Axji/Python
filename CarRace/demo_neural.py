"""Demo des neuronalen Netzes: Das gespeicherte Netz (brains/best_brain.json) fährt mehrere Rennen, ohne Spielerauto.

Das orange Auto fährt mit dem gespeicherten Netz, die rosa Autos mit leicht mutierten Kopien davon. Alle starten
gleichzeitig und kollidieren nicht. Für das orange Auto sind die Fühler (was das Netz "sieht") eingezeichnet.
Ein Auto, das von der Strasse abkommt oder stehen bleibt, bekommt ein Explosionsbild. Nach dem Rennen folgt ein neues
mit neuen Varianten.

Steuerung: Enter = nächstes Rennen sofort, Escape = beenden.

Aufruf (im Ordner CarRace):
    python demo_neural.py                 # endlos Rennen
    python demo_neural.py --races 3 --cars 12
Das Netz wird mit `python train_neural.py` trainiert.
"""
import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pygame

import constant
import neural_ai
import track_map as tm
from train_neural import ORANGE, PINK, SIGMAS, Race

FPS = 60
MAX_FRAMES = 1200
PAUSE_FRAMES = 150  # So lange bleibt das Ergebnis nach dem Rennen stehen
RAY_COLOR = (255, 60, 60)


def draw_race(screen, track_image, explosion, font, race, number, info):
    """Zeichnet Strecke, Autos, Fühler des orangen Autos und die Anzeige."""
    screen.blit(track_image, (0, 0))
    for i in reversed(range(len(race.cars))):  # das orange Auto (Nr. 0) zuletzt, damit es oben liegt
        c = race.cars[i]
        crashed = not race.alive[i] and race.finish_frame[i] is None
        if crashed:
            screen.blit(explosion, explosion.get_rect(center=(c.pos_x + 10, c.pos_y + 10)))
        else:
            screen.blit(c.getimage(), c.getPosAsRect())

    leader = race.cars[0]  # das Auto mit dem unveränderten gespeicherten Netz
    if race.alive[0]:
        cx, cy = leader.pos_x + 10, leader.pos_y + 10
        for angle in neural_ai.SENSOR_ANGLES:
            length = race.track_map.ray(cx, cy, leader.view_angle + angle, neural_ai.SENSOR_RANGE)
            end = (cx + math.cos(math.radians(leader.view_angle + angle)) * length,
                   cy + math.sin(math.radians(leader.view_angle + angle)) * length)
            pygame.draw.line(screen, RAY_COLOR, (cx, cy), end, 1)
            pygame.draw.circle(screen, RAY_COLOR, end, 3)
        pygame.draw.circle(screen, ORANGE, (cx, cy), 18, 2)

    finished = sum(1 for f in race.finish_frame if f is not None)
    lines = [
        f"Rennen {number}   Bild {race.frame}",
        f"Unterwegs: {sum(race.alive)}   Im Ziel: {finished}   Ausgeschieden: {len(race.cars) - sum(race.alive) - finished}",
        f"Orange: gespeichertes Netz (Bewertung {info.get('fitness', 0):.0f}, {info.get('races', '?')} Rennen gelernt)   "
        "Rosa: mutierte Varianten",
    ]
    for n, text in enumerate(lines):
        label = font.render(text, True, (255, 255, 255), (0, 0, 0))
        screen.blit(label, (10, 10 + n * 26))
    if race.over:
        times = sorted(f for f in race.finish_frame if f is not None)
        text = f"Rennen vorbei. Schnellste Zeit: {times[0]} Bilder ({times[0] / 30:.1f} s)" if times else "Rennen vorbei. Niemand im Ziel."
        screen.blit(font.render(text, True, (255, 255, 0), (0, 0, 0)), (10, 10 + len(lines) * 26))


def make_race(brain, track, count):
    """Rennen mit dem gespeicherten Netz (orange) und `count - 1` leicht mutierten Varianten (rosa)."""
    nets = [brain.copy()] + [brain.mutated(sigma=random.choice(SIGMAS)) for _ in range(count - 1)]
    return Race(nets, track, MAX_FRAMES, [ORANGE] + [PINK] * (count - 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--races", type=int, default=0, help="Anzahl Rennen (0 = endlos bis Escape)")
    parser.add_argument("--cars", type=int, default=10, help="Autos pro Rennen, Standard 10")
    parser.add_argument("--track", type=int, default=1, help="Nummer der Strecke (track_N.png)")
    args = parser.parse_args()

    brain, info = neural_ai.load_brain()
    if brain is None:
        print("Kein gespeichertes Netz gefunden. Zuerst trainieren: python train_neural.py --races 30")
        return

    pygame.init()
    screen = pygame.display.set_mode((constant.WINDOWWITH, constant.WINDOWHIGH))
    pygame.display.set_caption("NeuroSim - Demo neuronales Netz")
    font = pygame.font.SysFont(None, 26)
    track_image = pygame.image.load(f"track_{args.track}.png")
    explosion = pygame.image.load("explosion.png")
    track = tm.TrackMap(track_image)
    clock = pygame.time.Clock()

    number = 0
    running = True
    while running and (args.races == 0 or number < args.races):
        number += 1
        race = make_race(brain, track, args.cars)
        pause = 0
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    pause = PAUSE_FRAMES  # Rennen überspringen
                    race.max_frames = race.frame
            if not race.over:
                race.step()
            else:
                pause += 1
            draw_race(screen, track_image, explosion, font, race, number, info)
            pygame.display.update()
            clock.tick(FPS)
            if pause >= PAUSE_FRAMES:
                break
    pygame.quit()


if __name__ == "__main__":
    main()
