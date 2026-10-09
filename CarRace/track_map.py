"""Schnelle Streckenkarte für die lernende KI.

Aus dem Streckenbild wird einmal berechnet:
- welche Pixel befahrbar sind (Strasse und Ziellinie),
- der Fortschritt jedes Strassenpixels (Weglänge vom Start, per Breitensuche),
- ab welchem Fortschritt das Ziel erreicht ist.
Damit sind Fühler und Rennbewertung deutlich schneller als mit `Surface.get_at()`.
"""
import math
from collections import deque

import constant
import pygame

SENSOR_STEP = 4  # Schrittgrösse der Fühler in Pixeln


class TrackMap:
    def __init__(self, surface):
        self.width, self.height = surface.get_size()
        raw = pygame.image.tobytes(surface, "RGB")
        street = bytes(constant.COLOR_STREET[:3])
        finish = bytes(constant.COLOR_FINISH[:3])
        self.drivable = bytearray(self.width * self.height)
        finish_pixels = []
        for i in range(self.width * self.height):
            pixel = raw[i * 3:i * 3 + 3]
            if pixel == street:
                self.drivable[i] = 1
            elif pixel == finish:
                self.drivable[i] = 1
                finish_pixels.append(i)
        self._compute_progress(finish_pixels)

    def _compute_progress(self, finish_pixels):
        """Breitensuche vom Start aus: progress[i] = Weglänge in Pixeln, -1 = nicht erreichbar."""
        w, h = self.width, self.height
        self.progress = [-1] * (w * h)
        start = int(constant.STARTPOSY + constant.PLAYERHIGH / 2) * w + int(constant.STARTPOSX + constant.PLAYERWITH / 2)
        self.progress[start] = 0
        queue = deque([start])
        while queue:
            i = queue.popleft()
            d = self.progress[i] + 1
            x = i % w
            for j, ok in ((i - 1, x > 0), (i + 1, x < w - 1), (i - w, i >= w), (i + w, i < w * (h - 1))):
                if ok and self.drivable[j] and self.progress[j] < 0:
                    self.progress[j] = d
                    queue.append(j)
        reached = [self.progress[i] for i in finish_pixels if self.progress[i] >= 0]
        self.finish_progress = min(reached) if reached else max(self.progress)

    def is_drivable(self, x, y):
        x, y = int(x), int(y)
        return 0 <= x < self.width and 0 <= y < self.height and self.drivable[y * self.width + x] == 1

    def progress_at(self, x, y):
        """Fortschritt am Pixel (x, y) oder -1 neben der Strasse."""
        x, y = int(x), int(y)
        if not (0 <= x < self.width and 0 <= y < self.height):
            return -1
        return self.progress[y * self.width + x]

    def ray(self, x, y, angle_degrees, max_distance):
        """Freie Strasse in Pixeln ab (x, y) in Richtung `angle_degrees`, höchstens `max_distance`."""
        angle = math.radians(angle_degrees)
        dx, dy = math.cos(angle), math.sin(angle)
        dist = 0
        while dist < max_distance:
            if not self.is_drivable(x + dx * dist, y + dy * dist):
                break
            dist += SENSOR_STEP
        return dist
