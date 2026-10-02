"""Trainiert die lernende KI durch Auslese und Mutation (neuroevolutionärer Ansatz).

Jedes Rennen ist eine Generation: Alle Autos starten gleichzeitig am Start (leicht versetzt), jedes mit einem leicht
abweichenden Netz.
Die Autos kollidieren nicht miteinander. Ein Auto scheidet aus, wenn es die Strasse verlässt oder nicht mehr vorankommt.
Das Rennen endet, wenn alle Autos ausgeschieden oder im Ziel sind oder die Höchstdauer erreicht ist.
Danach werden die besten Netze behalten und mutiert; das beste Netz wird gespeichert (brains/best_brain.json) und
beim nächsten Training sowie im Spiel (main_myrace.py) wieder verwendet.

Aufruf (im Ordner CarRace):
    python train_neural.py --races 30            # 30 Rennen, ohne Fenster (schnell)
    python train_neural.py --races 10 --show     # mit Fenster zum Zuschauen
    python train_neural.py --fresh               # ohne das gespeicherte Netz neu anfangen
"""
import argparse
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import constant

FPS = 30
STUCK_FRAMES = 90        # So lange darf ein Auto ohne Fortschritt bleiben, bevor es ausscheidet
FINISH_BONUS = 3         # Zusatzpunkte pro Bild, das ein Auto vor der Höchstdauer im Ziel ist
ELITE = 4                # So viele beste Netze werden unverändert übernommen
PARENTS = 8              # Aus den besten so vielen Netzen entstehen die Nachkommen
NEWCOMERS = 3            # Zufällige neue Netze pro Generation (Vielfalt)
SIGMAS = (0.05, 0.15, 0.3)  # Mögliche Mutationsstärken der Nachkommen
START_JITTER_POS = 8     # Zufällige Abweichung der Startposition in Pixeln (macht das Gelernte robuster)
START_JITTER_ANGLE = 12  # Zufällige Abweichung der Startrichtung in Grad
PINK = (255, 130, 200)
ORANGE = (255, 150, 0)


def run_race(nets, track_map, max_frames, screen=None, generation=0):
    """Lässt alle Netze gleichzeitig ein Rennen fahren. Gibt pro Netz (Bewertung, im Ziel?, Zielbild) zurück."""
    import car
    import neural_ai

    cars = [car.Car(f"Net {i}", "car_1.png", ORANGE if i == 0 else PINK) for i in range(len(nets))]
    for c in cars:  # alle starten gleichzeitig, aber nicht exakt gleich
        c.pos_x += random.uniform(-START_JITTER_POS, START_JITTER_POS)
        c.pos_y += random.uniform(-START_JITTER_POS, START_JITTER_POS)
        c.view_angle = random.uniform(-START_JITTER_ANGLE, START_JITTER_ANGLE)
    drivers = [neural_ai.NeuralDriver(c, n) for c, n in zip(cars, nets)]
    best = [0] * len(nets)             # bester Fortschritt je Auto
    last_gain = [0] * len(nets)        # Bild des letzten Fortschritts
    alive = [True] * len(nets)
    finish_frame = [None] * len(nets)

    clock = None
    if screen is not None:
        import pygame
        clock = pygame.time.Clock()
        track_image = pygame.image.load(f"track_{track_map.number}.png")

    for frame in range(1, max_frames + 1):
        if not any(alive):
            break
        for i, (c, d) in enumerate(zip(cars, drivers)):
            if not alive[i]:
                continue
            d.drive(track_map)
            c.update()
            progress = track_map.progress_at(c.pos_x + constant.PLAYERWITH / 2, c.pos_y + constant.PLAYERHIGH / 2)
            if progress < 0:
                alive[i] = False          # von der Strasse abgekommen
                continue
            if progress > best[i]:
                best[i] = progress
                last_gain[i] = frame
            if best[i] >= track_map.finish_progress:
                alive[i] = False
                finish_frame[i] = frame   # im Ziel
            elif frame - last_gain[i] > STUCK_FRAMES:
                alive[i] = False          # kommt nicht mehr voran

        if screen is not None:
            import pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    raise KeyboardInterrupt
            screen.blit(track_image, (0, 0))
            for i, c in enumerate(cars):
                if alive[i] or finish_frame[i]:
                    screen.blit(c.getimage(), c.getPosAsRect())
            pygame.display.set_caption(f"Training - Rennen {generation}, Bild {frame}, aktiv: {sum(alive)}")
            pygame.display.update()
            clock.tick(FPS * 2)

    results = []
    for i in range(len(nets)):
        fitness = min(best[i], track_map.finish_progress)
        if finish_frame[i]:
            fitness += (max_frames - finish_frame[i]) * FINISH_BONUS
        results.append((fitness, finish_frame[i] is not None, finish_frame[i]))
    return results


def next_generation(ranked, population):
    """Neue Netze aus der nach Bewertung sortierten Liste: Elite unverändert, Nachkommen mutiert, ein paar Neulinge."""
    import neural_ai

    new = [n.copy() for n in ranked[:ELITE]]
    parents = ranked[:PARENTS]
    while len(new) < population - NEWCOMERS:
        new.append(random.choice(parents).mutated(rate=0.2, sigma=random.choice(SIGMAS)))
    while len(new) < population:
        new.append(neural_ai.NeuralNet())
    return new


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--races", type=int, default=30, help="Anzahl Rennen (Generationen), Standard 30")
    parser.add_argument("--population", type=int, default=40, help="Autos pro Rennen, Standard 40")
    parser.add_argument("--max-frames", type=int, default=1200, help="Höchstdauer eines Rennens in Bildern")
    parser.add_argument("--track", type=int, default=1, help="Nummer der Strecke (track_N.png)")
    parser.add_argument("--show", action="store_true", help="Rennen in einem Fenster anzeigen")
    parser.add_argument("--fresh", action="store_true", help="Gespeichertes Netz ignorieren und neu anfangen")
    args = parser.parse_args()

    if not args.show:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame
    import neural_ai
    import track_map as tm

    pygame.init()
    screen = pygame.display.set_mode((constant.WINDOWWITH, constant.WINDOWHIGH)) if args.show else None
    t0 = time.time()
    track = tm.TrackMap(pygame.image.load(f"track_{args.track}.png"))
    track.number = args.track
    print(f"Streckenkarte berechnet ({time.time() - t0:.1f} s), Ziel bei Fortschritt {track.finish_progress}")

    saved_net, info = (None, {}) if args.fresh else neural_ai.load_brain()
    saved_fitness = info.get("fitness", -1) if saved_net else -1
    total_races = info.get("races", 0) if saved_net else 0
    if saved_net:
        print(f"Starte vom gespeicherten Netz (Bewertung {saved_fitness}, {total_races} Rennen gelernt)")
        nets = [saved_net.copy()] + [saved_net.mutated(sigma=random.choice(SIGMAS))
                                     for _ in range(args.population - 1 - NEWCOMERS)]
        nets += [neural_ai.NeuralNet() for _ in range(NEWCOMERS)]
    else:
        print("Kein gespeichertes Netz: Start mit Zufallsnetzen")
        nets = [neural_ai.NeuralNet() for _ in range(args.population)]

    best_fitness, best_net = saved_fitness, saved_net
    races_done = 0
    try:
        for race in range(1, args.races + 1):
            t0 = time.time()
            results = run_race(nets, track, args.max_frames, screen, total_races + race)
            order = sorted(range(len(nets)), key=lambda i: -results[i][0])
            ranked = [nets[i] for i in order]
            top = results[order[0]]
            finished = sum(1 for r in results if r[1])
            mean = sum(r[0] for r in results) / len(results)
            print(f"Rennen {race:3d}/{args.races}: beste {top[0]:6.0f} | Schnitt {mean:6.0f} | im Ziel {finished:2d}/{len(nets)}"
                  + (f" | schnellste Zeit {top[2]} Bilder" if top[1] else "") + f" | {time.time() - t0:.1f} s")
            if top[0] > best_fitness:
                best_fitness, best_net = top[0], ranked[0].copy()
                neural_ai.save_brain(best_net, best_fitness, races=total_races + race, track=args.track)
                print("   -> neues bestes Netz gespeichert")
            nets = next_generation(ranked, args.population)
            races_done = race
    except KeyboardInterrupt:
        print("Training abgebrochen")
    if best_net is not None and best_fitness > saved_fitness:  # Zähler der gelernten Rennen aktualisieren
        neural_ai.save_brain(best_net, best_fitness, races=total_races + races_done, track=args.track)
    print(f"Beste Bewertung: {best_fitness:.0f} (gespeichert in {neural_ai.BRAIN_FILE})")
    pygame.quit()


if __name__ == "__main__":
    main()
