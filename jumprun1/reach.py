"""Misst mit der echten Spielphysik, was Einzel- und Doppelsprung schaffen.

Die Messung baut zwei Plattformen mit einer Lücke von `gap` Kacheln, lässt die Figur mit gedrückter Rechts-Taste
losrennen und probiert alle Absprungpunkte und alle Zeitpunkte des zweiten Sprungs durch. So hängt der Level-Generator
nicht an von Hand geschätzten Zahlen: ändert man die Physik in `constants.py`, passt sich die Tabelle an.
"""
import os
from functools import lru_cache

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from .entities import Player  # noqa: E402
from .level import LEVEL_HEIGHT, Level  # noqa: E402
from .constants import TILE  # noqa: E402

LEFT_COLS = 8          # Anlauf auf der linken Plattform
RIGHT_COLS = 8         # Länge der Zielplattform
BASE_ROW = 6           # Oberkante der linken Plattform
MAX_FRAMES = 220
MAX_DELAY = 70         # so viele Bilder nach dem ersten Sprung wird der zweite probiert


def _grid(gap, rise):
    """Zwei Plattformen; die rechte liegt `rise` Kacheln höher (negativ: tiefer)."""
    right_row = BASE_ROW - rise
    grid = [["."] * (LEFT_COLS + gap + RIGHT_COLS) for _ in range(LEVEL_HEIGHT)]
    for col in range(len(grid[0])):
        if col < LEFT_COLS:
            top = BASE_ROW
        elif col >= LEFT_COLS + gap:
            top = right_row
        else:
            continue
        for row in range(top, LEVEL_HEIGHT):
            grid[row][col] = "#"
    return grid


def _attempt(level, goal_col, goal_top, trigger_x, second_delay):
    """Eine Probe: rechts halten, bei `trigger_x` springen, `second_delay` Bilder später noch einmal (None = nie)."""
    player = Player(2 * TILE, BASE_ROW * TILE + _y_offset() - Player.HEIGHT)
    for _ in range(5):
        player.update(level, False, False, False)
    jump_frame = None
    for frame in range(MAX_FRAMES):
        if jump_frame is None and player.pos.x >= trigger_x:
            player.request_jump()
            jump_frame = frame
        elif second_delay is not None and jump_frame is not None and frame == jump_frame + second_delay:
            player.request_jump()
        player.update(level, False, True, True)
        if player.rect.top > level.height:
            return False
        if player.on_ground and player.rect.bottom == goal_top and player.rect.centerx >= goal_col * TILE:
            return True
    return False


def _y_offset():
    from .level import Y_OFFSET
    return Y_OFFSET


@lru_cache(maxsize=None)
def _apex_frame():
    """Nach wie vielen Bildern ist der erste Sprung am höchsten Punkt?"""
    level = Level(_grid(4, 0))
    player = Player(2 * TILE, BASE_ROW * TILE + _y_offset() - Player.HEIGHT)
    for _ in range(5):
        player.update(level, False, False, False)
    player.request_jump()
    for frame in range(60):
        player.update(level, False, True, True)
        if player.vel.y >= 0:
            return frame
    return 30


def can_cross(gap, rise, mode):
    """Schafft die Figur diese Lücke (in Kacheln) mit diesem Höhenunterschied (in Kacheln, + = Ziel höher)?

    mode: "single"  nur ein Sprung,
          "early"   Doppelsprung, der zweite Sprung spätestens im höchsten Punkt des ersten,
          "double"  Doppelsprung mit beliebigem Zeitpunkt (auch verzögert im Fallen).
    """
    level = Level(_grid(gap, rise))
    goal_col = LEFT_COLS + gap
    goal_top = (BASE_ROW - rise) * TILE + _y_offset()
    edge = LEFT_COLS * TILE
    if mode == "single":
        delays = [None]
    elif mode == "early":
        delays = range(1, _apex_frame() + 1)
    else:
        delays = range(1, MAX_DELAY)
    for trigger_x in range(edge - 70, edge + 16, 2):
        for delay in delays:
            if _attempt(level, goal_col, goal_top, trigger_x, delay):
                return True
    return False


@lru_cache(maxsize=None)
def max_gap(rise, mode):
    """Grösste Lückenbreite in Kacheln, die bei diesem Höhenunterschied noch geht (-1: schon Lücke 0 geht nicht)."""
    best = -1
    for gap in range(0, 14):
        if can_cross(gap, rise, mode):
            best = gap
        elif gap > best + 1:
            break
    return best
