"""Der Spielplan: ein Raster aus Kacheln, dazu Startpunkte von Figur, Gegnern, Münzen und Ziel.

Zeichen im Raster:
    .  leer          #  Erde/Gras        B  Ziegel        ?  Fragezeichen-Block (fest, ohne Wirkung)
    P  Start         E  Gegner           C  Münze          F  Ziel (Fahne)
"""
import pygame

from .constants import SCREEN_H, TILE

LEVEL_WIDTH = 80          # Spalten
LEVEL_HEIGHT = 11         # Zeilen
GROUND_ROWS = 2           # die untersten zwei Zeilen sind Boden
GAPS = [(21, 23), (41, 43), (58, 60), (66, 68)]  # Löcher im Boden (von Spalte, bis Spalte), je 3 Kacheln breit
SOLID = "#B?"             # Zeichen, durch die man nicht hindurchkommt
Y_OFFSET = SCREEN_H - LEVEL_HEIGHT * TILE  # schiebt den Plan nach unten, damit er den Bildschirm genau füllt


def build_grid():
    """Baut das Raster auf. Hier lässt sich der Plan ändern oder ein eigener entwerfen."""
    grid = [["."] * LEVEL_WIDTH for _ in range(LEVEL_HEIGHT)]
    ground_top = LEVEL_HEIGHT - GROUND_ROWS  # Zeile 9; Figuren stehen auf Zeile 8

    def put(col, row, char):
        grid[row][col] = char

    def span(col_from, col_to, row, char):
        for col in range(col_from, col_to + 1):
            put(col, row, char)

    # Boden mit Löchern
    for col in range(LEVEL_WIDTH):
        if not any(a <= col <= b for a, b in GAPS):
            for row in range(ground_top, LEVEL_HEIGHT):
                put(col, row, "#")

    put(2, 8, "P")
    span(6, 8, 8, "C")                       # Münzen am Boden

    span(8, 11, 7, "B")                      # kleine Plattform zum Hinaufspringen
    put(9, 7, "?")
    put(10, 7, "?")
    span(12, 14, 5, "B")                     # zweite, höhere Plattform (nicht vor dem Loch, sonst stösst man beim Absprung an)
    span(12, 14, 4, "C")
    span(21, 23, 6, "C")                     # Münzen über dem ersten Loch

    span(31, 32, 7, "B")                     # Mauer, an der Gegner umkehren
    span(31, 32, 8, "B")

    span(45, 47, 7, "B")                     # Plattform hinter dem zweiten Loch
    span(45, 47, 6, "C")
    span(49, 53, 8, "C")

    for height, col in enumerate(range(71, 75), start=1):  # Treppe zum Ziel: jede Spalte eine Kachel höher
        for k in range(height):
            put(col, 8 - k, "B")

    for col in (12, 28, 36, 50, 54, 64):
        put(col, 8, "E")
    put(77, 8, "F")
    return grid


class Level:
    """Hält das Raster und liefert Kollisionsflächen sowie Startpunkte."""

    def __init__(self):
        self.grid = build_grid()
        self.width = LEVEL_WIDTH * TILE
        self.height = LEVEL_HEIGHT * TILE + Y_OFFSET
        self.player_start = (0, 0)
        self.enemy_starts = []
        self.coins = []
        self.flag_rect = pygame.Rect(0, 0, 0, 0)
        self.goal_rect = pygame.Rect(0, 0, 0, 0)  # Zielzone: wie die Fahne, aber bis zum oberen Rand, damit man sie nicht überspringt
        self._find_objects()

    def _find_objects(self):
        for row, line in enumerate(self.grid):
            for col, char in enumerate(line):
                x, y = col * TILE, row * TILE + Y_OFFSET
                if char == "P":
                    self.player_start = (x + 2, y)
                elif char == "E":
                    self.enemy_starts.append((x + 2, y + 4))
                elif char == "C":
                    self.coins.append(pygame.Rect(x + 4, y + 4, 8, 8))
                elif char == "F":
                    self.flag_rect = pygame.Rect(x, y - 2 * TILE, TILE, 3 * TILE)  # 3 Kacheln hoch, unten auf dem Boden
                    self.goal_rect = pygame.Rect(x, -10 * TILE, TILE, 10 * TILE + y + TILE)
                if char in "PECF":
                    self.grid[row][col] = "."  # Objekte sind keine Kacheln

    def char_at(self, col, row):
        """Kachelzeichen an Spalte/Zeile. Links und rechts ist der Plan von Wänden begrenzt, oben und unten offen."""
        if col < 0 or col >= LEVEL_WIDTH:
            return "#"
        if row < 0 or row >= LEVEL_HEIGHT:
            return "."
        return self.grid[row][col]

    def is_solid(self, col, row):
        return self.char_at(col, row) in SOLID

    def is_solid_at(self, x, y):
        """Ist an diesem Bildpunkt (Weltkoordinaten) etwas Festes?"""
        return self.is_solid(int(x) // TILE, (int(y) - Y_OFFSET) // TILE)

    def solid_rects_near(self, rect):
        """Alle festen Kacheln in der Nähe eines Rechtecks, als Rechtecke in Weltkoordinaten."""
        rects = []
        for row in range((rect.top - Y_OFFSET) // TILE - 1, (rect.bottom - Y_OFFSET) // TILE + 2):
            for col in range(rect.left // TILE - 1, rect.right // TILE + 2):
                if self.is_solid(col, row):
                    rects.append(pygame.Rect(col * TILE, row * TILE + Y_OFFSET, TILE, TILE))
        return rects
