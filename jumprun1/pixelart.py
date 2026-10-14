"""Alle Grafiken des Spiels. Es werden keine Bilddateien geladen: Figuren, Kacheln und Hintergrund entstehen beim Start
aus Textbildern und einfachen Zeichenbefehlen.

Ein Textbild besteht aus Zeilen gleicher Länge. Jedes Zeichen steht für eine Farbe aus PALETTE, der Punkt ist
durchsichtig.
"""
import math
import random

import pygame

from .constants import SCREEN_H, SCREEN_W, TILE

PALETTE = {
    "r": (214, 48, 49),    # rot (Mütze, Pullover)
    "s": (250, 196, 150),  # Haut
    "k": (60, 36, 28),     # dunkelbraun (Haare, Augen)
    "b": (52, 92, 200),    # blau (Latzhose)
    "w": (255, 255, 255),  # weiss
    "n": (110, 64, 32),    # braun (Schuhe)
    "g": (150, 150, 160),  # grau (Waffe)
    "y": (252, 214, 50),   # gelb
    "o": (200, 140, 20),   # orange (Münzrand)
    "m": (160, 96, 48),    # Pilzbraun
    "h": (128, 78, 40),    # Hut (Abenteurer-Hut)
    "H": (60, 34, 18),     # Hutband
    "l": (236, 176, 64),   # blonde Haare
    "t": (96, 140, 200),   # Hemd (hellblau)
    "p": (170, 124, 70),   # Hose (Khaki)
    "u": (58, 36, 24),     # Stiefel und Gürtel
}

# Abenteurer im Stil von Rick Dangerous: Hut mit breiter Krempe, blonde Haare, hellblaues Hemd, Khakihose, Stiefel
# und eine Pistole. Die Figur schaut nach rechts und hält die Waffe vorne (Zeile 7). Die Beine (Zeilen 12 bis 15)
# unterscheiden sich je Bild.
PLAYER_BODY = [
    "....hhhh....",
    "...hhhhhh...",
    "...HHHHHH...",
    ".hhhhhhhhhh.",
    "...lssssss..",
    "...lssssks..",
    "....sssss...",
    "..tttttttsgg",
    "..sttttttt..",
    "...tttttt...",
    "...uuuuuu...",
    "...pppppp...",
]
PLAYER_LEGS = {
    "idle": ["..pp..pp....", "..pp..pp....", "..uu..uu....", ".uuu..uuu..."],
    "run1": ["..pp...pp...", "..pp....pp..", "..uu....uu..", ".uuu...uuu.."],
    "run2": ["...pp.pp....", "....ppp.....", "....uuu.....", "...uuuuu...."],
    "jump": ["..pp...pp...", ".pp.....pp..", ".uu.....uu..", "............"],
}

ENEMY_HEAD = [
    "....mmmm....",
    "..mmmmmmmm..",
    ".mmmmmmmmmm.",
    ".mwwmmmmwwm.",
    ".mwkmmmmkwm.",
    "mmmmmmmmmmmm",
    "mmmmmmmmmmmm",
    ".mmmmmmmmmm.",
    "...ssssss...",
    "..ssssssss..",
]
ENEMY_FEET = {
    "a": ["..nn....nn..", ".nnnn..nnnn."],
    "b": ["...nn..nn...", "..nnnn.nnnn."],
}

COIN = [
    "..oooo..",
    ".oyyyyo.",
    "oyywyyyo",
    "oyywyyyo",
    "oyyyyyyo",
    "oyyyyyyo",
    ".oyyyyo.",
    "..oooo..",
]
BULLET = [
    "..yyy.",
    "wyyyyy",
    "..yyy.",
]
QUESTION_MARK = [
    "..yyyy..",
    ".yy..yy.",
    ".....yy.",
    "....yy..",
    "...yy...",
    "........",
    "...yy...",
    "........",
]


def from_ascii(rows, palette=PALETTE):
    """Wandelt ein Textbild in eine Fläche mit durchsichtigem Hintergrund um."""
    width = len(rows[0])
    surface = pygame.Surface((width, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f"Zeile {y} ist {len(row)} Zeichen lang, erwartet {width}: {row!r}")
        for x, char in enumerate(row):
            if char != ".":
                surface.set_at((x, y), palette[char])
    return surface


def flipped(surface):
    """Spiegelt eine Figur links/rechts."""
    return pygame.transform.flip(surface, True, False)


class PlayerSprites:
    """Alle Bilder der Spielfigur, je einmal nach rechts und nach links schauend."""

    def __init__(self):
        right = {name: from_ascii(PLAYER_BODY + legs) for name, legs in PLAYER_LEGS.items()}
        self.frames = {1: right, -1: {name: flipped(img) for name, img in right.items()}}

    def get(self, facing, state):
        return self.frames[facing][state]


def enemy_frames():
    """Zwei Laufbilder des Gegners (die Füsse wechseln)."""
    return [from_ascii(ENEMY_HEAD + feet) for feet in ENEMY_FEET.values()]


def coin_sprite():
    return from_ascii(COIN)


def bullet_sprites():
    """Kugel nach rechts und nach links."""
    right = from_ascii(BULLET)
    return {1: right, -1: flipped(right)}


def _speckled(color, speckles, rng, size=TILE, count=14):
    """Kachel in einer Grundfarbe mit zufälligen Pixeln, wirkt wie Erde oder Stein."""
    tile = pygame.Surface((size, size))
    tile.fill(color)
    for _ in range(count):
        tile.set_at((rng.randrange(size), rng.randrange(size)), rng.choice(speckles))
    return tile


def make_tiles():
    """Kacheln für Erde, Gras, Ziegel und Fragezeichen-Block."""
    rng = random.Random(7)
    dirt = _speckled((140, 84, 40), [(110, 62, 28), (166, 106, 56)], rng)

    grass = dirt.copy()
    pygame.draw.rect(grass, (84, 176, 60), (0, 0, TILE, 4))
    for x in range(0, TILE, 2):  # ausgefranster Rand nach unten
        grass.set_at((x, 4), (84, 176, 60))
        if rng.random() < 0.5:
            grass.set_at((x, 5), (60, 140, 44))
    for _ in range(4):
        grass.set_at((rng.randrange(TILE), rng.randrange(3)), (130, 214, 96))

    brick = pygame.Surface((TILE, TILE))
    brick.fill((178, 74, 52))
    mortar = (110, 40, 30)
    for y in (7, 15):
        pygame.draw.line(brick, mortar, (0, y), (TILE - 1, y))
    for x in (7,):
        pygame.draw.line(brick, mortar, (x, 0), (x, 6))
    for x in (3, 11):
        pygame.draw.line(brick, mortar, (x, 8), (x, 14))

    block = pygame.Surface((TILE, TILE))
    block.fill((240, 180, 40))
    pygame.draw.rect(block, (160, 100, 20), (0, 0, TILE, TILE), 1)
    for corner in ((2, 2), (TILE - 3, 2), (2, TILE - 3), (TILE - 3, TILE - 3)):
        block.set_at(corner, (160, 100, 20))
    mark = from_ascii(QUESTION_MARK, {"y": (130, 80, 10)})
    block.blit(mark, (4, 4))

    return {"dirt": dirt, "grass": grass, "brick": brick, "block": block}


def flag_sprite():
    """Zielfahne: Stange mit grünem Tuch, drei Kacheln hoch."""
    flag = pygame.Surface((TILE, TILE * 3), pygame.SRCALPHA)
    pygame.draw.rect(flag, (220, 220, 230), (2, 0, 2, TILE * 3))
    pygame.draw.rect(flag, (252, 214, 50), (1, 0, 4, 3))  # Kugel oben
    for row in range(8):  # Dreieck aus Zeilen, jede Zeile etwas schmaler
        pygame.draw.line(flag, (60, 190, 90), (4, 3 + row), (TILE - 2 - row, 3 + row))
    return flag


class Background:
    """Pixeliger Hintergrund aus Himmelsstreifen, Wolken und zwei Hügelreihen, die verschieden schnell scrollen."""

    SKY = [(92, 148, 252), (112, 164, 252), (132, 180, 252), (156, 196, 252), (180, 212, 252)]

    def __init__(self):
        self.sky = self._make_sky()
        # (Fläche, Scrollfaktor): kleiner Faktor = weit weg = bewegt sich langsamer als die Kamera
        self.layers = [
            (self._make_clouds(), 0.1),
            (self._make_hills(30, 14, (88, 168, 112), (112, 192, 128), 2, 0.3), 0.25),
            (self._make_hills(22, 12, (56, 140, 88), (84, 168, 100), 3, 1.7), 0.5),
        ]

    def _make_sky(self):
        sky = pygame.Surface((SCREEN_W, SCREEN_H))
        band = SCREEN_H // len(self.SKY) + 1
        for i, color in enumerate(self.SKY):
            pygame.draw.rect(sky, color, (0, i * band, SCREEN_W, band))
            if i > 0:  # Übergang mit Schachbrett-Zeile (Dithering) wie bei alten Spielen
                for x in range(0, SCREEN_W, 2):
                    sky.set_at((x + i % 2, i * band), color)
                    sky.set_at((x + (i + 1) % 2, i * band - 1), self.SKY[i - 1])
        return sky

    @staticmethod
    def _make_clouds(width=640):
        layer = pygame.Surface((width, SCREEN_H), pygame.SRCALPHA)
        for cx, cy in ((60, 30), (190, 55), (330, 25), (470, 60), (590, 35)):
            for dx, dy, w, h in ((8, 0, 24, 6), (0, 6, 40, 8), (4, 14, 32, 4)):  # Wolke aus drei Rechtecken
                pygame.draw.rect(layer, (255, 255, 255), (cx + dx, cy + dy, w, h))
            pygame.draw.rect(layer, (214, 226, 246), (cx + 4, cy + 14, 32, 4))  # Schatten unten
        return layer

    @staticmethod
    def _make_hills(base_height, amplitude, color, light, waves, phase, width=480):
        """Hügel aus 4 Pixel breiten Säulen. Ganze Wellen pro Breite sorgen für eine nahtlose Kachelung."""
        layer = pygame.Surface((width, SCREEN_H), pygame.SRCALPHA)
        ground = SCREEN_H - 20
        for x in range(0, width, 4):
            height = base_height + amplitude * math.sin(x / width * 2 * math.pi * waves + phase)
            height = int(height) // 4 * 4  # in 4er-Stufen, damit die Hänge treppenartig aussehen
            pygame.draw.rect(layer, color, (x, ground - height, 4, height + 20))
            pygame.draw.rect(layer, light, (x, ground - height, 4, 2))
        return layer

    def draw(self, surface, camera_x):
        surface.blit(self.sky, (0, 0))
        for layer, factor in self.layers:
            width = layer.get_width()
            offset = -int(camera_x * factor) % width
            surface.blit(layer, (offset - width, 0))
            surface.blit(layer, (offset, 0))
