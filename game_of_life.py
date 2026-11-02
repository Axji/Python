"""Conways Game of Life mit pygame-ce.

Auf einem Gitter aus Zellen leben oder sterben die Zellen nach vier Regeln (B3/S23):
  - Eine lebende Zelle mit weniger als 2 lebenden Nachbarn stirbt (Einsamkeit).
  - Eine lebende Zelle mit 2 oder 3 lebenden Nachbarn überlebt.
  - Eine lebende Zelle mit mehr als 3 lebenden Nachbarn stirbt (Überbevölkerung).
  - Eine tote Zelle mit genau 3 lebenden Nachbarn wird lebendig.

Bedienung:
    Linke Maustaste (halten)    Zellen setzen, auch beim Ziehen über mehrere Felder
    Rechte Maustaste (halten)   Zellen löschen
    Leertaste                   Start / Stop
    S oder Pfeil rechts         genau einen Schritt (eine Generation) weiter
    C                           alles löschen
    Z                           Zufallsfeld
    T                           Rand umschalten: Torus (rechts geht es links weiter) oder fester Rand
    + / -  (oder Bild auf/ab)   schneller / langsamer
    Esc                         beenden
Alle Funktionen gibt es auch als Knöpfe oben im Fenster. Gezeichnet werden darf jederzeit, auch während die Simulation läuft.

Aufruf:  python game_of_life.py
"""
import random
from collections import Counter

import pygame

COLS = 80             # Anzahl Zellen waagrecht
ROWS = 50             # Anzahl Zellen senkrecht
CELL = 12             # Kantenlänge einer Zelle in Pixeln
TOOLBAR_H = 76        # Höhe der Leiste oben mit Knöpfen und Anzeige
FPS = 60
SPEEDS = [1, 2, 4, 8, 15, 30, 60]  # Schritte pro Sekunde, wenn die Simulation läuft
START_SPEED = 3       # Index in SPEEDS (8 Schritte pro Sekunde)
RANDOM_DENSITY = 0.25  # Anteil lebender Zellen beim Zufallsfeld

BACKGROUND = (22, 24, 30)
GRID_LINE = (36, 40, 48)
ALIVE = (110, 220, 140)
TOOLBAR = (34, 38, 48)
BUTTON = (58, 66, 84)
BUTTON_HOVER = (78, 90, 114)
BUTTON_ACTIVE = (70, 140, 100)
TEXT = (232, 236, 244)
TEXT_DIM = (150, 158, 172)


# ---------------------------------------------------------------- Spiellogik (ohne pygame, einzeln testbar)

def next_generation(live, cols, rows, wrap=True):
    """Berechnet die nächste Generation. `live` ist die Menge der lebenden Zellen als (Spalte, Zeile).

    Mit `wrap=True` ist das Feld ein Torus: Was rechts hinausfliegt, kommt links wieder herein. Mit `wrap=False` ist
    ausserhalb des Felds alles tot.
    """
    neighbors = Counter()  # für jede Zelle neben einer lebenden: wie viele lebende Nachbarn hat sie?
    for col, row in live:
        for d_col in (-1, 0, 1):
            for d_row in (-1, 0, 1):
                if d_col == 0 and d_row == 0:
                    continue
                n_col, n_row = col + d_col, row + d_row
                if wrap:
                    n_col, n_row = n_col % cols, n_row % rows
                elif not (0 <= n_col < cols and 0 <= n_row < rows):
                    continue
                neighbors[(n_col, n_row)] += 1
    return {cell for cell, count in neighbors.items() if count == 3 or (count == 2 and cell in live)}


def cells_on_line(start, end):
    """Alle Zellen auf der Strecke von `start` nach `end` (beide eingeschlossen), damit schnelles Ziehen keine Lücken lässt."""
    (col, row), (end_col, end_row) = start, end
    d_col, d_row = abs(end_col - col), -abs(end_row - row)
    step_col = 1 if col < end_col else -1
    step_row = 1 if row < end_row else -1
    error = d_col + d_row
    cells = []
    while True:
        cells.append((col, row))
        if (col, row) == (end_col, end_row):
            return cells
        double_error = 2 * error
        if double_error >= d_row:
            error += d_row
            col += step_col
        if double_error <= d_col:
            error += d_col
            row += step_row


def random_field(cols, rows, density=RANDOM_DENSITY, rng=random):
    """Zufällig verteilte lebende Zellen, `density` ist der ungefähre Anteil (0 bis 1)."""
    return {(col, row) for col in range(cols) for row in range(rows) if rng.random() < density}


# ---------------------------------------------------------------- Oberfläche

class Button:
    """Ein Knopf in der Leiste. `label` ist ein Text oder eine Funktion, die den aktuellen Text liefert.

    `texts` listet alle Texte, die der Knopf annehmen kann. Die Breite richtet sich nach dem längsten, damit der Knopf
    beim Umschalten (Start/Stop) nicht die Grösse ändert.
    """

    def __init__(self, label, action, is_active=None, texts=None):
        self.label = label
        self.action = action
        self.is_active = is_active  # Funktion: soll der Knopf hervorgehoben sein?
        self.texts = texts or [label]
        self.rect = pygame.Rect(0, 0, 0, 0)

    def text(self):
        return self.label() if callable(self.label) else self.label


class LifeApp:
    """Fenster, Eingaben und der aktuelle Spielstand."""

    def __init__(self, cols=COLS, rows=ROWS, cell=CELL):
        self.cols, self.rows, self.cell = cols, rows, cell
        self.live = set()
        self.generation = 0
        self.running = False
        self.wrap = True
        self.speed_index = START_SPEED
        self.last_step_ms = 0
        self.drag_last = None   # zuletzt bearbeitete Zelle beim Ziehen, für lückenlose Linien
        self.drag_alive = True  # True = beim Ziehen Zellen setzen, False = löschen

        pygame.init()
        pygame.display.set_caption("Game of Life")
        self.window = pygame.display.set_mode((cols * cell, TOOLBAR_H + rows * cell))
        self.font = pygame.font.SysFont("segoeui,arial,verdana,dejavusans", 16, bold=True)
        self.small_font = pygame.font.SysFont("segoeui,arial,verdana,dejavusans", 14)
        self.clock = pygame.time.Clock()

        self.buttons = [
            Button(lambda: "Stop" if self.running else "Start", self.toggle_running, lambda: self.running, ["Start", "Stop"]),
            Button("Schritt", self.step),
            Button("Löschen", self.clear),
            Button("Zufall", self.randomize),
            Button("Langsamer", self.slower),
            Button("Schneller", self.faster),
            Button(lambda: "Rand: Torus" if self.wrap else "Rand: fest", self.toggle_wrap, texts=["Rand: Torus", "Rand: fest"]),
        ]
        self.layout_buttons()

    # ----------------------------------------------------------- Aktionen

    def toggle_running(self):
        self.running = not self.running
        self.last_step_ms = pygame.time.get_ticks()

    def step(self):
        """Genau eine Generation weiter, auch wenn die Simulation gerade steht."""
        self.live = next_generation(self.live, self.cols, self.rows, self.wrap)
        self.generation += 1

    def clear(self):
        self.live.clear()
        self.generation = 0
        self.running = False

    def randomize(self):
        self.live = random_field(self.cols, self.rows)
        self.generation = 0

    def slower(self):
        self.speed_index = max(0, self.speed_index - 1)

    def faster(self):
        self.speed_index = min(len(SPEEDS) - 1, self.speed_index + 1)

    def toggle_wrap(self):
        self.wrap = not self.wrap

    @property
    def speed(self):
        return SPEEDS[self.speed_index]

    # ----------------------------------------------------------- Zellen mit der Maus setzen und löschen

    def cell_at(self, pos):
        """Zelle unter dem Mauszeiger als (Spalte, Zeile). Kann ausserhalb des Felds liegen, auch in der Leiste."""
        x, y = pos
        return x // self.cell, (y - TOOLBAR_H) // self.cell

    def in_field(self, cell):
        col, row = cell
        return 0 <= col < self.cols and 0 <= row < self.rows

    def paint(self, cell):
        """Setzt oder löscht Zellen von der zuletzt bearbeiteten bis zu dieser Zelle (eine Linie ohne Lücken)."""
        start = self.drag_last if self.drag_last is not None else cell
        for line_cell in cells_on_line(start, cell):
            if self.in_field(line_cell):
                if self.drag_alive:
                    self.live.add(line_cell)
                else:
                    self.live.discard(line_cell)
        self.drag_last = cell

    # ----------------------------------------------------------- Ereignisse

    def handle_event(self, event):
        """Verarbeitet ein pygame-Ereignis. Gibt False zurück, wenn das Programm beendet werden soll."""
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            return self.handle_key(event.key)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            if event.pos[1] < TOOLBAR_H:
                if event.button == 1:
                    self.click_toolbar(event.pos)
                return True
            self.drag_alive = event.button == 1  # linke Taste setzt, rechte löscht
            self.drag_last = None
            self.paint(self.cell_at(event.pos))
        elif event.type == pygame.MOUSEMOTION and self.drag_last is not None:
            if event.buttons[0] or event.buttons[2]:
                self.drag_alive = bool(event.buttons[0])
                self.paint(self.cell_at(event.pos))
            else:
                self.drag_last = None
        elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            self.drag_last = None
        return True

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            return False
        actions = {
            pygame.K_SPACE: self.toggle_running,
            pygame.K_s: self.step,
            pygame.K_RIGHT: self.step,
            pygame.K_c: self.clear,
            pygame.K_z: self.randomize,
            pygame.K_t: self.toggle_wrap,
            pygame.K_PLUS: self.faster,
            pygame.K_KP_PLUS: self.faster,
            pygame.K_EQUALS: self.faster,
            pygame.K_PAGEUP: self.faster,
            pygame.K_MINUS: self.slower,
            pygame.K_KP_MINUS: self.slower,
            pygame.K_PAGEDOWN: self.slower,
        }
        if key in actions:
            actions[key]()
        return True

    def click_toolbar(self, pos):
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                button.action()
                return

    # ----------------------------------------------------------- Ablauf

    def update(self, now_ms):
        """Rechnet einen Schritt, wenn die Simulation läuft und seit dem letzten Schritt genug Zeit vergangen ist."""
        if self.running and now_ms - self.last_step_ms >= 1000 / self.speed:
            self.last_step_ms = now_ms
            self.step()

    def run(self):
        keep_going = True
        while keep_going:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    keep_going = False
            self.update(pygame.time.get_ticks())
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    # ----------------------------------------------------------- Zeichnen

    def layout_buttons(self):
        """Ordnet die Knöpfe in einer Reihe oben an. Die Breite richtet sich nach dem längsten möglichen Text."""
        padding, gap, x = 16, 8, 8
        for button in self.buttons:
            width = max(self.font.size(text)[0] for text in button.texts) + 2 * padding
            button.rect = pygame.Rect(x, 8, width, 34)
            x += width + gap

    def draw(self):
        self.window.fill(BACKGROUND)
        self.draw_field()
        self.draw_toolbar()
        pygame.display.flip()

    def draw_field(self):
        size = self.cell
        for col in range(self.cols + 1):  # feine Gitterlinien
            x = col * size
            pygame.draw.line(self.window, GRID_LINE, (x, TOOLBAR_H), (x, TOOLBAR_H + self.rows * size))
        for row in range(self.rows + 1):
            y = TOOLBAR_H + row * size
            pygame.draw.line(self.window, GRID_LINE, (0, y), (self.cols * size, y))
        for col, row in self.live:
            self.window.fill(ALIVE, (col * size + 1, TOOLBAR_H + row * size + 1, size - 1, size - 1))

    def draw_toolbar(self):
        pygame.draw.rect(self.window, TOOLBAR, (0, 0, self.window.get_width(), TOOLBAR_H))
        mouse = pygame.mouse.get_pos()
        for button in self.buttons:
            if button.is_active and button.is_active():
                color = BUTTON_ACTIVE
            elif button.rect.collidepoint(mouse):
                color = BUTTON_HOVER
            else:
                color = BUTTON
            pygame.draw.rect(self.window, color, button.rect, border_radius=6)
            label = self.font.render(button.text(), True, TEXT)
            self.window.blit(label, label.get_rect(center=button.rect.center))

        state = "läuft" if self.running else "gestoppt"
        status = (f"Generation {self.generation}   Lebende Zellen {len(self.live)}   "
                  f"Tempo {self.speed}/s   {state}")
        self.window.blit(self.font.render(status, True, TEXT), (10, 48))
        hint = "Links halten: zeichnen   Rechts halten: löschen   Leertaste: Start/Stop   S: Schritt"
        hint_image = self.small_font.render(hint, True, TEXT_DIM)
        self.window.blit(hint_image, (self.window.get_width() - hint_image.get_width() - 10, 52))


def main():
    LifeApp().run()


if __name__ == "__main__":
    main()
