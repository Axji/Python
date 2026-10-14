"""Spielfigur, Gegner und Kugeln samt Physik (Schwerkraft, Kollision mit den Kacheln)."""
from dataclasses import dataclass, field

import pygame

from .constants import (
    AIR_CONTROL,
    AIR_JUMP_SPEED,
    BULLET_LIFETIME,
    BULLET_SPEED,
    COIN_POP_FRAMES,
    COYOTE_FRAMES,
    ENEMY_SPEED,
    FRICTION,
    GRAVITY,
    INVULNERABLE_FRAMES,
    JUMP_BUFFER_FRAMES,
    JUMP_RELEASE_SPEED,
    JUMP_SPEED,
    MAX_BULLETS,
    MAX_FALL,
    MAX_JUMPS,
    RUN_ACCEL,
    RUN_MAX,
    SHOOT_COOLDOWN,
)


@dataclass
class MoveResult:
    """Was bei einem Bewegungsschritt passiert ist."""

    on_ground: bool = False
    hit_wall: bool = False
    hit_ceiling: bool = False
    ceiling_tiles: list = field(default_factory=list)  # Kacheln, an die der Kopf gestossen ist


def move_body(body, level):
    """Bewegt einen Körper um seine Geschwindigkeit und löst Zusammenstösse mit festen Kacheln auf.

    `body` braucht `pos` (genaue Lage als Vector2), `vel` und `rect` (ganzzahlige Lage für Kollisionen). Erst wird in
    x-Richtung bewegt und korrigiert, dann in y-Richtung. So bleibt die Figur an Wänden nicht hängen.
    """
    result = MoveResult()

    body.pos.x += body.vel.x
    body.rect.x = round(body.pos.x)
    for tile in level.solid_rects_near(body.rect):
        if body.rect.colliderect(tile):
            if body.vel.x > 0:
                body.rect.right = tile.left
            elif body.vel.x < 0:
                body.rect.left = tile.right
            body.pos.x = body.rect.x
            result.hit_wall = True

    body.pos.y += body.vel.y
    body.rect.y = round(body.pos.y)
    for tile in level.solid_rects_near(body.rect):
        if body.rect.colliderect(tile):
            if body.vel.y > 0:
                body.rect.bottom = tile.top
                result.on_ground = True
            elif body.vel.y < 0:
                body.rect.top = tile.bottom
                result.hit_ceiling = True
                result.ceiling_tiles.append(tile)
            body.pos.y = body.rect.y
            body.vel.y = 0

    # Steht der Körper schon auf dem Boden? Die Schwerkraft schiebt ihn pro Bild nur um Bruchteile eines Pixels, das
    # rundet wieder auf die alte Lage, und es gäbe keinen Zusammenstoss. Ohne diese Prüfung würde der Körper jedes zweite
    # Bild als "in der Luft" gelten (die Beine der Figur flackerten).
    if not result.on_ground and body.vel.y >= 0:
        feet = body.rect.move(0, 1)
        if any(feet.colliderect(tile) for tile in level.solid_rects_near(feet)):
            result.on_ground = True
            body.pos.y = body.rect.y
            body.vel.y = 0

    return result


class Bullet:
    """Eine Kugel, die immer waagrecht geradeaus fliegt."""

    WIDTH, HEIGHT = 6, 3

    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(round(x), round(y), self.WIDTH, self.HEIGHT)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(direction * BULLET_SPEED, 0)
        self.direction = direction
        self.life = BULLET_LIFETIME
        self.alive = True

    def update(self, level):
        self.pos += self.vel
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        self.life -= 1
        if self.life <= 0 or any(self.rect.colliderect(t) for t in level.solid_rects_near(self.rect)):
            self.alive = False


class Player:
    """Die Spielfigur: läuft, springt (je länger die Taste, desto höher), kann einmal in der Luft nachspringen
    (Doppelsprung) und schiesst geradeaus nach vorne. Nach dem zweiten Sprung muss sie erst landen."""

    WIDTH, HEIGHT = 12, 16
    GUN_HEIGHT = 6  # Abstand des Laufs von der Oberkante der Figur

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.facing = 1          # 1 = nach rechts, -1 = nach links
        self.on_ground = False
        self.coyote = 0          # Restzeit, in der nach dem Verlassen einer Kante noch gesprungen werden darf
        self.jump_buffer = 0     # Restzeit, in der ein früh gedrückter Sprung noch gilt
        self.jumps_used = 0      # Sprünge seit der letzten Landung (der Absprung vom Boden zählt als erster)
        self.ceiling_tiles = []
        self.shoot_cooldown = 0
        self.invulnerable = 0    # Restzeit der Schutzphase nach einem Treffer
        self.anim = 0

    def respawn(self, x, y):
        """Stellt die Figur wieder an den Start (nach einem Sturz)."""
        self.pos.update(x, y)
        self.rect.topleft = (x, y)
        self.vel.update(0, 0)
        self.invulnerable = INVULNERABLE_FRAMES

    def request_jump(self):
        """Wird beim Drücken der Sprungtaste aufgerufen; der Sprung wird kurz gemerkt."""
        self.jump_buffer = JUMP_BUFFER_FRAMES

    def hurt(self, from_x):
        """Treffer durch einen Gegner: Schutzphase und Rückstoss weg vom Gegner."""
        self.invulnerable = INVULNERABLE_FRAMES
        self.vel.y = -3.0
        self.vel.x = 2.0 if self.rect.centerx >= from_x else -2.0

    def try_shoot(self, bullets):
        """Schiesst geradeaus in Blickrichtung, falls Pause und Obergrenze es erlauben. Gibt die Kugel zurück oder None."""
        if self.shoot_cooldown > 0 or len(bullets) >= MAX_BULLETS:
            return None
        self.shoot_cooldown = SHOOT_COOLDOWN
        x = self.rect.right if self.facing > 0 else self.rect.left - Bullet.WIDTH
        return Bullet(x, self.rect.y + self.GUN_HEIGHT, self.facing)

    def update(self, level, left, right, jump_held):
        direction = int(right) - int(left)

        # Seitlich beschleunigen oder abbremsen
        accel = RUN_ACCEL if self.on_ground else RUN_ACCEL * AIR_CONTROL
        if direction:
            self.vel.x += direction * accel
            self.facing = direction
        elif self.on_ground:
            self.vel.x = max(0.0, self.vel.x - FRICTION) if self.vel.x > 0 else min(0.0, self.vel.x + FRICTION)
        self.vel.x = max(-RUN_MAX, min(RUN_MAX, self.vel.x))

        # Springen: kurz nach der Kante (coyote) und kurz vor der Landung (buffer) wird verziehen
        if self.on_ground:
            self.coyote = COYOTE_FRAMES
            self.jumps_used = 0  # gelandet: beide Sprünge sind wieder frei
        else:
            self.coyote = max(0, self.coyote - 1)
            if self.coyote == 0 and self.jumps_used == 0:
                self.jumps_used = 1  # von einer Kante gefallen: der Sprung vom Boden ist verfallen, einer bleibt
        self.jump_buffer = max(0, self.jump_buffer - 1)
        if self.jump_buffer and (self.coyote or self.jumps_used < MAX_JUMPS):
            from_ground = bool(self.coyote)
            self.vel.y = -(JUMP_SPEED if from_ground else AIR_JUMP_SPEED)
            self.jumps_used = 1 if from_ground else self.jumps_used + 1
            self.jump_buffer = self.coyote = 0
        if not jump_held and self.vel.y < -JUMP_RELEASE_SPEED:
            self.vel.y = -JUMP_RELEASE_SPEED  # Taste losgelassen: kurzer Sprung

        self.vel.y = min(self.vel.y + GRAVITY, MAX_FALL)
        result = move_body(self, level)
        self.on_ground = result.on_ground
        self.ceiling_tiles = result.ceiling_tiles  # Kacheln, an die der Kopf in diesem Bild gestossen ist (Fragezeichen-Blöcke)
        if result.hit_wall:
            self.vel.x = 0

        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
        self.invulnerable = max(0, self.invulnerable - 1)
        self.anim += 1

    @property
    def sprite_state(self):
        """Welches Bild gerade passt: Sprung, Lauf (zwei Bilder im Wechsel) oder Stand."""
        if not self.on_ground:
            return "jump"
        if abs(self.vel.x) > 0.3:
            return "run1" if (self.anim // 7) % 2 == 0 else "run2"
        return "idle"


class Enemy:
    """Ein Läufer, der hin und her geht und an Wänden und Kanten umkehrt."""

    WIDTH, HEIGHT = 12, 12

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.direction = -1
        self.alive = True
        self.anim = 0

    def update(self, level):
        self.vel.x = self.direction * ENEMY_SPEED
        self.vel.y = min(self.vel.y + GRAVITY, MAX_FALL)
        result = move_body(self, level)
        if result.hit_wall or (result.on_ground and not self._ground_ahead(level)):
            self.direction = -self.direction
        self.anim += 1

    def _ground_ahead(self, level):
        """Gibt es vor dem Gegner noch Boden? Sonst würde er in ein Loch laufen."""
        x = self.rect.right + 1 if self.direction > 0 else self.rect.left - 2
        return level.is_solid_at(x, self.rect.bottom + 1)

    @property
    def frame(self):
        return (self.anim // 12) % 2


class CoinPop:
    """Eine Münze, die aus einem Block nach oben springt und zurückfällt. Nur Bewegung: die Punkte gibt es sofort."""

    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, -3.2)
        self.life = COIN_POP_FRAMES

    @property
    def alive(self):
        return self.life > 0

    def update(self):
        self.vel.y += 0.25
        self.pos += self.vel
        self.life -= 1
