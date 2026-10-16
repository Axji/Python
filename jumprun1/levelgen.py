"""Zufallsgenerator für die Pläne ab Level 2.

Die generierten Pläne sind doppelt so lang wie Level 1 (`GENERATED_WIDTH` Spalten). Das Gelände besteht aus Plattformen
(Erdsäulen bis zum unteren Rand), die durch Lücken getrennt sind und verschieden hoch liegen. Jedes Hindernis gehört
zu einer von sieben Sorten (siehe `KINDS`); die Masse stammen aus `REACH`, einer Tabelle der Reichweiten von Einzel-
und Doppelsprung:

- Nichts ist unmöglich: keine Lücke und keine Stufe geht über das hinaus, was der Doppelsprung schafft.
- Einiges ist mit dem Einzelsprung unmöglich (breite Lücken, hohe Mauern), es braucht den Doppelsprung.
- Die "Drops" (tiefer liegende Landung hinter einer sehr breiten Lücke) schafft man nur, wenn man den zweiten Sprung
  verzögert, also erst im Fallen auslöst: so wird die Strecke am weitesten.

Die Tabelle wurde mit `reach.py` gemessen (echte Spielphysik); `tests/test_jumprun1.py` prüft sie gegen die Physik nach.
"""
import random
from dataclasses import dataclass

from .level import GROUND_ROWS, LEVEL_HEIGHT, LEVEL_WIDTH

GENERATED_WIDTH = 2 * LEVEL_WIDTH   # doppelt so lang wie Level 1
GROUND_ROW = LEVEL_HEIGHT - GROUND_ROWS  # Oberkante des Bodens im Startbereich (Zeile 9)
MIN_ROW = 3                         # höchste erlaubte Plattform-Oberkante
START_COLS = 8                      # Länge der Startplattform
FINAL_COLS = 9                      # so lang ist die Zielplattform mindestens
MAX_TRIES = 60                      # Versuche pro Hindernis, bevor abgebrochen wird

# Reichweite pro Höhenunterschied `rise` (in Kacheln, + = Ziel liegt höher), gemessen mit reach.py.
# Erstes Tripel (single, early, double) = grösste Lückenbreite in Kacheln, die mit Einzelsprung / Doppelsprung im
# höchsten Punkt / Doppelsprung mit beliebigem Zeitpunkt überhaupt noch geht (-1: nicht einmal ohne Lücke).
# Zweites Tripel = grösste Breite, die man mit breitem Absprungfenster schafft; die Lücken des Generators halten sich
# daran, damit sie fair bleiben.
REACH = {
    -4: ((6, 8, 9), (5, 7, 8)),
    -3: ((5, 8, 9), (5, 7, 8)),
    -2: ((5, 8, 9), (5, 7, 8)),
    -1: ((5, 7, 8), (4, 7, 8)),
    0: ((5, 7, 8), (4, 6, 7)),
    1: ((4, 7, 8), (4, 6, 7)),
    2: ((4, 6, 7), (3, 6, 7)),
    3: ((3, 6, 7), (2, 5, 6)),
    4: ((-1, 6, 6), (-1, 5, 6)),
    5: ((-1, 5, 6), (-1, 5, 5)),
}
# Lückenbreiten, die man nur mit verzögertem Doppelsprung schafft (breiter als im höchsten Punkt möglich) und die
# trotzdem ein brauchbares Fenster lassen: Höhenunterschied -> Breiten
DELAYED_GAPS = {-1: (8,), -3: (9,), -4: (9,)}


@dataclass(frozen=True)
class Step:
    """Ein Hindernis: `gap` leere Kacheln, danach liegt die Plattform `rise` Kacheln höher, ab Spalte `col`."""

    kind: str
    gap: int
    rise: int
    col: int  # erste Spalte der Lücke (bzw. der Stufe)


def _rises(candidates, row):
    """Die Höhenunterschiede aus `candidates`, bei denen die neue Plattform noch im erlaubten Bereich liegt."""
    return [r for r in candidates if MIN_ROW <= row - r <= GROUND_ROW]


def _pick(rng, low, high, t):
    """Zufallszahl zwischen `low` und `high`; je grösser die Schwierigkeit `t` (0..1), desto näher am oberen Ende."""
    high = low + round((high - low) * (0.4 + 0.6 * t))
    return rng.randint(low, max(low, high))


def _single_gap(rng, row, t=0.0):
    """Lücke, die auch mit einem Sprung geht."""
    rise = rng.choice(_rises((-2, -1, 0, 1, 2), row))
    return _pick(rng, 2, REACH[rise][1][0], t), rise


def _double_gap(rng, row, t=0.0):
    """Lücke, die nur mit Doppelsprung geht: breiter als der Einzelsprung je schafft."""
    rise = rng.choice(_rises((-3, -2, -1, 0, 1, 2, 3), row))
    return _pick(rng, REACH[rise][0][0] + 1, REACH[rise][1][1], t), rise


def _delayed_drop(rng, row, t=0.0):
    """Tiefer gelegene Landung hinter einer Lücke, die nur mit verzögertem Doppelsprung zu schaffen ist."""
    options = [(r, g) for r, gaps in DELAYED_GAPS.items() for g in gaps if MIN_ROW <= row - r <= GROUND_ROW]
    rise, gap = rng.choice(options)
    return gap, rise


def _wall_single(rng, row, t=0.0):
    """Mauer, die man mit einem Sprung erklimmt."""
    return 0, rng.choice(_rises((1, 2, 3), row))


def _wall_double(rng, row, t=0.0):
    """Mauer, für die der Einzelsprung zu niedrig ist."""
    return 0, rng.choice(_rises((4, 5), row))


def _step_down(rng, row, t=0.0):
    """Abstieg ohne Lücke."""
    return 0, rng.choice(_rises((-1, -2, -3, -4), row))


def _gap_up(rng, row, t=0.0):
    """Lücke mit höher liegender Landung, die nur mit Doppelsprung geht."""
    rise = rng.choice(_rises((2, 3, 4, 5), row))
    low = REACH[rise][0][0] + 1 if REACH[rise][0][0] >= 0 else 1
    return _pick(rng, low, max(low, REACH[rise][1][1]), t), rise


# Sorte -> (Erzeuger, Gewicht in Level 2, Zuwachs des Gewichts pro Level, ob nur mit Doppelsprung machbar)
# Level 2 ist mild: gut zwei Drittel der Hindernisse gehen mit dem Einzelsprung. Mit jedem Level werden die leichten
# Sorten seltener und die Doppelsprung-Sorten häufiger, und die Lücken werden breiter.
KINDS = {
    "single_gap": (_single_gap, 5, -0.5, False),
    "wall_single": (_wall_single, 3, -0.3, False),
    "step_down": (_step_down, 3, -0.3, False),
    "double_gap": (_double_gap, 2, 0.8, True),
    "wall_double": (_wall_double, 1, 0.5, True),
    "delayed_drop": (_delayed_drop, 0.5, 0.5, True),
    "gap_up": (_gap_up, 0.5, 0.4, True),
}
MAX_LEVEL = 10      # ab hier wird es nicht mehr schwerer
MIN_WEIGHT = 0.5    # leichte Sorten verschwinden nie ganz


def difficulty(number):
    """Schwierigkeit 0.0 (Level 2) bis 1.0 (Level `MAX_LEVEL`)."""
    return max(0.0, min(1.0, (number - 2) / (MAX_LEVEL - 2)))


def required(number):
    """Sorten, von denen ein Plan dieses Levels mindestens ein Hindernis haben muss."""
    return ("double_gap", "wall_double") if number <= 2 else ("double_gap", "wall_double", "delayed_drop")


def weight(kind, number):
    _, base, per_level, _ = KINDS[kind]
    return max(MIN_WEIGHT, base + per_level * (min(number, MAX_LEVEL) - 2))


def _possible(kind, row):
    """Gibt es von dieser Höhe aus ein Hindernis dieser Sorte?"""
    try:
        KINDS[kind][0](random.Random(0), row, 0.0)
    except IndexError:  # leere Auswahl: in dieser Höhe nicht möglich
        return False
    return True


def plan(seed, number=2):
    """Legt die Folge der Hindernisse fest. Gleiche `seed`/`number` ergeben denselben Plan.

    Gibt (Schritte, Plattformen) zurück; Plattformen sind (erste Spalte, Spalte hinter dem Ende, Zeile der Oberkante).
    Je höher das Level, desto häufiger sind die Sorten, die den Doppelsprung brauchen, und desto breiter die Lücken.
    """
    for attempt in range(500):
        rng = random.Random(f"{seed}-{number}-{attempt}")
        steps, platforms = _try_plan(rng, number)
        if steps and all(any(s.kind == k for s in steps) for k in required(number)):
            return steps, platforms
    raise RuntimeError("Kein passender Plan gefunden")  # praktisch unmöglich, die Hürde ist niedrig


def _try_plan(rng, number):
    platforms = [(0, START_COLS, GROUND_ROW)]
    steps = []
    cursor, row = START_COLS, GROUND_ROW
    while cursor < GENERATED_WIDTH - FINAL_COLS:
        kinds = [k for k in KINDS if _possible(k, row)]
        weights = [weight(k, number) + (2 if k == "step_down" and row <= 5 else 0) for k in kinds]
        for _ in range(MAX_TRIES):
            kind = rng.choices(kinds, weights)[0]
            gap, rise = KINDS[kind][0](rng, row, difficulty(number))
            width = rng.randint(6, 11)
            end = cursor + gap + width
            if GENERATED_WIDTH - end < FINAL_COLS:  # zu nah am Rand: die Plattform bis zum Ende ziehen
                end = GENERATED_WIDTH
                width = end - cursor - gap
            if width >= (FINAL_COLS if end == GENERATED_WIDTH else 4):
                break
        else:
            # Nichts passt mehr: die letzte Plattform bis zum Rand verlängern
            start, _, last_row = platforms[-1]
            platforms[-1] = (start, GENERATED_WIDTH, last_row)
            return steps, platforms
        steps.append(Step(kind, gap, rise, cursor))
        row -= rise
        platforms.append((cursor + gap, end, row))
        cursor = end
    start, _, last_row = platforms[-1]
    platforms[-1] = (start, GENERATED_WIDTH, last_row)  # die letzte Plattform reicht immer bis zum Rand
    return steps, platforms


def generate_grid(seed, number=2):
    """Baut das Raster für Level `number` (2, 3, ...) aus `seed`. Zeichen wie in `level.py`."""
    _, platforms = plan(seed, number)
    rng = random.Random(f"{seed}-{number}-deko")
    grid = [["."] * GENERATED_WIDTH for _ in range(LEVEL_HEIGHT)]

    def put(col, row, char):
        if 0 <= row < LEVEL_HEIGHT and grid[row][col] == ".":
            grid[row][col] = char

    for start, end, top in platforms:
        for col in range(start, end):
            for row in range(top, LEVEL_HEIGHT):
                grid[row][col] = "#"

    grid[GROUND_ROW - 1][2] = "P"
    last = len(platforms) - 1
    for index, (start, end, top) in enumerate(platforms):
        width = end - start
        if index > 0 and index != last and width >= 6:
            enemies = 1 + (width >= 10 and number >= 4)
            for k in range(enemies):
                put(start + width // 2 + 2 * k - (enemies - 1), top - 1, "E")
        if width >= 9 and index != 0:  # Ziegelstreifen mit Block, weit weg von den Kanten (stört keinen Absprung)
            left, right = start + 4, end - 6
            if right - left >= 2:
                brick = rng.randint(3, min(5, right - left + 1))
                first = rng.randint(left, right - brick + 1)
                for col in range(first, first + brick):
                    put(col, top - 3, "?" if col == first + brick // 2 else "B")
        if index != last and width >= 5:  # Münzen am Boden
            first = start + rng.randint(1, max(1, width - 5))
            for col in range(first, min(first + 3, end - 1)):
                put(col, top - 1, "C")
        if index > 0:  # Münzen im Bogen über der Lücke davor
            prev_end, prev_top = platforms[index - 1][1], platforms[index - 1][2]
            gap = start - prev_end
            if gap >= 2:
                for col in range(prev_end + gap // 2 - 1, prev_end + gap // 2 + 2):
                    if prev_end <= col < start:
                        put(col, min(prev_top, top) - 3, "C")
    # Ziel: Fahne 3 Kacheln vor dem rechten Rand auf der letzten Plattform
    flag_col, flag_row = GENERATED_WIDTH - 3, platforms[-1][2] - 1
    for row in range(LEVEL_HEIGHT):  # nichts im Weg der Fahne
        if grid[row][flag_col] in "CE":
            grid[row][flag_col] = "."
    grid[flag_row][flag_col] = "F"
    return ["".join(row) for row in grid]


def profile(grid):
    """Liest aus einem Raster das Gelände ab: (Lücke, Höhenunterschied) zwischen aufeinanderfolgenden Plattformen.

    Lücke = Anzahl Spalten ohne Boden (0 bei einer Stufe), Höhenunterschied in Kacheln (+ = die nächste Plattform
    liegt höher). Plattformen gleicher Höhe ohne Lücke zählen als eine.
    """
    tops = [next((r for r in range(len(grid)) if grid[r][col] == "#"), None) for col in range(len(grid[0]))]
    result = []
    col = 0
    while col < len(tops) - 1:
        nxt = col + 1
        while nxt < len(tops) and tops[nxt] is None:
            nxt += 1
        if nxt < len(tops) and (nxt > col + 1 or tops[nxt] != tops[col]):
            result.append((nxt - col - 1, tops[col] - tops[nxt]))
        col = nxt
    return result
