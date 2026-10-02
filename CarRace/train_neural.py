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


class Race:
    """Ein Rennen, bei dem alle Netze gleichzeitig starten. `step()` rechnet ein Bild weiter."""

    def __init__(self, nets, track_map, max_frames, colors=None):
        import car
        import neural_ai

        self.track_map = track_map
        self.max_frames = max_frames
        self.frame = 0
        colors = colors or [PINK] * len(nets)
        self.cars = [car.Car(f"Net {i}", "car_1.png", colors[i]) for i in range(len(nets))]
        for c in self.cars:  # alle starten gleichzeitig, aber nicht exakt gleich
            c.pos_x += random.uniform(-START_JITTER_POS, START_JITTER_POS)
            c.pos_y += random.uniform(-START_JITTER_POS, START_JITTER_POS)
            c.view_angle = random.uniform(-START_JITTER_ANGLE, START_JITTER_ANGLE)
        self.drivers = [neural_ai.NeuralDriver(c, n) for c, n in zip(self.cars, nets)]
        self.best = [0] * len(nets)             # bester Fortschritt je Auto
        self.last_gain = [0] * len(nets)        # Bild des letzten Fortschritts
        self.alive = [True] * len(nets)
        self.finish_frame = [None] * len(nets)
        self.end_frame = [None] * len(nets)     # Bild, in dem das Auto ausgeschieden oder im Ziel ist

    @property
    def over(self):
        """True, wenn alle Autos ausgeschieden oder im Ziel sind oder die Höchstdauer erreicht ist."""
        return not any(self.alive) or self.frame >= self.max_frames

    def step(self):
        self.frame += 1
        for i, (c, d) in enumerate(zip(self.cars, self.drivers)):
            if not self.alive[i]:
                continue
            d.drive(self.track_map)
            c.update()
            progress = self.track_map.progress_at(c.pos_x + constant.PLAYERWITH / 2, c.pos_y + constant.PLAYERHIGH / 2)
            if progress < 0:
                self.alive[i] = False          # von der Strasse abgekommen
                self.end_frame[i] = self.frame
                continue
            if progress > self.best[i]:
                self.best[i] = progress
                self.last_gain[i] = self.frame
            if self.best[i] >= self.track_map.finish_progress:
                self.alive[i] = False
                self.finish_frame[i] = self.frame   # im Ziel
                self.end_frame[i] = self.frame
            elif self.frame - self.last_gain[i] > STUCK_FRAMES:
                self.alive[i] = False          # kommt nicht mehr voran
                self.end_frame[i] = self.frame

    def results(self):
        """Pro Netz (Bewertung, im Ziel?, Zielbild, Bilder bis zum Ende des Autos)."""
        out = []
        for i in range(len(self.cars)):
            fitness = min(self.best[i], self.track_map.finish_progress)
            if self.finish_frame[i]:
                fitness += (self.max_frames - self.finish_frame[i]) * FINISH_BONUS
            out.append((fitness, self.finish_frame[i] is not None, self.finish_frame[i],
                        self.end_frame[i] or self.frame))
        return out


def draw_frames_per_car(screen, results, order, font):
    """Legt eine Tabelle über das Fenster: Bilder jedes Autos (beste zuerst) und ob es im Ziel war."""
    import pygame

    rows = []
    for rank, i in enumerate(order, start=1):
        fitness, finished, finish_frame, end_frame = results[i]
        rows.append((f"{rank:2d}. Auto {i:2d}: {end_frame:4d} Bilder  " + ("Ziel" if finished else "ausgeschieden"),
                     (120, 255, 120) if finished else (255, 140, 140)))
    per_column = (len(rows) + 1) // 2
    panel = pygame.Surface((2 * 330 + 20, per_column * 22 + 40))
    panel.fill((0, 0, 0))
    panel.blit(font.render("Bilder je Auto in diesem Rennen", True, (255, 255, 0)), (10, 8))
    for n, (text, color) in enumerate(rows):
        panel.blit(font.render(text, True, color), (10 + (n // per_column) * 330, 34 + (n % per_column) * 22))
    panel.set_alpha(225)
    screen.blit(panel, (constant.WINDOWWITH // 2 - panel.get_width() // 2, 80))
    pygame.display.update()


def run_race(nets, track_map, max_frames, screen=None, generation=0):
    """Lässt alle Netze ein Rennen fahren (optional im Fenster). Gibt `Race.results()` zurück."""
    colors = [ORANGE] + [PINK] * (len(nets) - 1)
    race = Race(nets, track_map, max_frames, colors)
    if screen is not None:
        import pygame
        clock = pygame.time.Clock()
        track_image = pygame.image.load(f"track_{track_map.number}.png")
    while not race.over:
        race.step()
        if screen is not None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    raise KeyboardInterrupt
            screen.blit(track_image, (0, 0))
            for i, c in enumerate(race.cars):
                if race.alive[i] or race.finish_frame[i]:
                    screen.blit(c.getimage(), c.getPosAsRect())
            pygame.display.set_caption(f"Training - Rennen {generation}, Bild {race.frame}, aktiv: {sum(race.alive)}")
            pygame.display.update()
            clock.tick(FPS * 2)
    results = race.results()
    if screen is not None:  # Ergebnis-Tabelle kurz anzeigen
        order = sorted(range(len(nets)), key=lambda i: -results[i][0])
        draw_frames_per_car(screen, results, order, pygame.font.SysFont(None, 22))
        for _ in range(FPS * 3):
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    raise KeyboardInterrupt
            clock.tick(FPS)
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
            in_goal = sorted(r[3] for r in results if r[1])
            out = sorted((r[3] for r in results if not r[1]), reverse=True)
            print("   Bilder im Ziel:        " + (" ".join(map(str, in_goal)) or "-"))
            print("   Bilder ausgeschieden:  " + (" ".join(map(str, out)) or "-"))
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
