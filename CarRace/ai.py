"""Eine sehr einfache KI, die ein Auto steuert.

Die KI "sieht" mit drei Fühlern (links, geradeaus, rechts) wie weit die Strasse vor dem Auto noch frei ist:
- Lenken: zur Seite mit mehr freier Strasse.
- Tempo: je weniger geradeaus frei ist, desto langsamer das Wunschtempo (Gas bzw. Bremse bis dahin).

Sie bedient das Auto genau wie ein Mensch über `delta_speed` und `delta_view_angle`.
"""
import math
import random

import constant

SENSOR_ANGLE = 40     # Winkel der seitlichen Fühler in Grad
SENSOR_RANGE = 150    # Reichweite der Fühler in Pixeln
SPEED_LOOKAHEAD = 260 # So weit voraus schaut die KI für das Wunschtempo (früher bremsen vor engen Kurven)
SENSOR_STEP = 4       # Schrittgrösse beim Abtasten
STEER_TOLERANCE = 8   # Unterschied links/rechts, ab dem gelenkt wird
MISTAKE_CHANCE = 0.002  # Wahrscheinlichkeit pro Bild für einen Fahrfehler
CAR_BRAKE_DISTANCE = 28  # Näher als das hinter einem Auto: nicht schneller als dieses fahren
OVERTAKE_RANGE = 80    # Ein langsameres Auto so weit voraus (in Pixeln) löst ein Überholmanöver aus
OVERTAKE_LANE = 20     # Seitlicher Abstand, bis zu dem ein Auto als "direkt voraus" gilt
OVERTAKE_PUSH = 40     # Wie stark zur Überholseite gelenkt wird (wirkt wie lane_bias)
OVERTAKE_MIN_FRONT = 100  # Ist geradeaus weniger Strasse frei (Kurve), wird nicht überholt
OVERTAKE_HOLD = 20     # Bilder, die das Manöver nach dem letzten Sichtkontakt noch anhält
AVOID_RANGE = 48       # Abstand der Autos (Mitte zu Mitte), ab dem seitlich ausgewichen wird
AVOID_PUSH = 60        # Stärke des Ausweichens (wirkt wie lane_bias, wird mit der Vorsicht multipliziert)
WALL_MARGIN = 40       # Näher als das an der Strassenkante wird nicht mehr in diese Richtung ausgewichen
LEADER_CAUTION = 0.4   # Vorsicht des Führenden im Verhältnis zu den anderen (weniger entschlossen)
MIN_SPEED = 3         # Tempo, das auch in engen Kurven gefahren wird


def _is_drivable(color):
    return tuple(color) in (constant.COLOR_STREET, constant.COLOR_FINISH)


class AIDriver:
    """Steuert ein `Car`. Jeder Fahrer variiert leicht (zufällig bei der Erstellung und laufend), damit nicht alle
    Autos identisch fahren:
    - `boldness`: Grundtempo (1 = normal, kleiner = vorsichtiger)
    - `lane_bias`: bevorzugte Seite der Strasse in Pixeln (negativ = links, positiv = rechts)
    - Tempo- und Lenkrauschen sowie seltene kleine Fahrfehler
    - `caution`: wie stark Kollisionen vermieden werden; der Führende weicht nur mit LEADER_CAUTION davon aus
    Überholen: Ein Auto direkt voraus wird nicht abgebremst, sondern auf der Seite mit mehr Platz umfahren.
    Die Fühler messen nur die Strasse; andere Autos in `obstacles` werden separat erkannt (Überholen, Abstand halten).
    """

    def __init__(self, car, boldness=1.0, sensor_angle=SENSOR_ANGLE, variation=1.0, obstacles=()):
        self.car = car
        self.obstacles = obstacles
        self.variation = variation
        self.boldness = boldness * random.uniform(1 - 0.08 * variation, 1 + 0.08 * variation)
        self.sensor_angle = sensor_angle + random.uniform(-6, 6) * variation
        self.lane_bias = random.uniform(-10, 10) * variation
        self.caution = random.uniform(1 - 0.2 * variation, 1 + 0.2 * variation)
        self.mistake_frames = 0   # Restdauer eines laufenden Fahrfehlers
        self.mistake_steer = 0
        self.overtake_side = 0    # -1 = links überholen, 1 = rechts, 0 = kein Manöver
        self.overtake_frames = 0  # Restdauer des Manövers

    def distance(self, track, offset, max_distance=SENSOR_RANGE):
        """Freie Strecke in Pixeln in Richtung Blickwinkel + offset (Grad), gemessen auf dem Streckenbild."""
        angle = math.radians(self.car.view_angle + offset)
        cx = self.car.pos_x + constant.PLAYERWITH / 2
        cy = self.car.pos_y + constant.PLAYERHIGH / 2
        dist = 0
        while dist < max_distance:
            x = int(cx + math.cos(angle) * dist)
            y = int(cy + math.sin(angle) * dist)
            if not (0 <= x < track.get_width() and 0 <= y < track.get_height()):
                break
            if not _is_drivable(track.get_at((x, y))):
                break
            dist += SENSOR_STEP
        return dist

    def _car_ahead(self):
        """Nächstes Auto direkt voraus als (Abstand nach vorn, seitlicher Versatz, Auto) oder None.
        Seitlich positiv = rechts von uns."""
        angle = math.radians(self.car.view_angle)
        fx, fy = math.cos(angle), math.sin(angle)
        best = None
        for other in self.obstacles:
            if other is self.car:
                continue
            dx = other.pos_x - self.car.pos_x
            dy = other.pos_y - self.car.pos_y
            forward = dx * fx + dy * fy
            lateral = -dx * fy + dy * fx
            if 0 < forward < OVERTAKE_RANGE and abs(lateral) < OVERTAKE_LANE:
                if best is None or forward < best[0]:
                    best = (forward, lateral, other)
        return best

    def _avoid_push(self, left, right):
        """Seitliches Ausweichen vor Autos, die neben oder vor uns nahe sind (positiv = nach rechts lenken).

        Der Führende weicht schwächer aus (LEADER_CAUTION), damit er seine Linie hält und nicht ausgebremst wird.
        Zur Strassenkante hin wird nicht ausgewichen.
        """
        angle = math.radians(self.car.view_angle)
        fx, fy = math.cos(angle), math.sin(angle)
        leader = all(o.distance_driven <= self.car.distance_driven for o in self.obstacles if o is not self.car)
        caution = self.caution * (LEADER_CAUTION if leader else 1)
        push = 0
        for other in self.obstacles:
            if other is self.car:
                continue
            dx = other.pos_x - self.car.pos_x
            dy = other.pos_y - self.car.pos_y
            dist = math.hypot(dx, dy)
            forward = dx * fx + dy * fy
            lateral = -dx * fy + dy * fx
            if dist >= AVOID_RANGE or forward < -constant.PLAYERHIGH or abs(lateral) < 4:
                continue  # zu weit weg, hinter uns (der kümmert sich selbst) oder genau davor (Überholen)
            closeness = (AVOID_RANGE - dist) / (AVOID_RANGE - constant.PLAYERWITH)
            push -= (1 if lateral > 0 else -1) * min(1, closeness)
        push *= AVOID_PUSH * caution
        if (push > 0 and right < WALL_MARGIN) or (push < 0 and left < WALL_MARGIN):
            push = 0
        return push

    def drive(self, track):
        """Entscheidet für dieses Bild über Gas/Bremse und Lenkung. `track` ist das Bild der aktuellen Strecke."""
        left = self.distance(track, -self.sensor_angle)
        front = self.distance(track, 0)
        right = self.distance(track, self.sensor_angle)

        # Überholen: Auto direkt voraus -> auf der Seite mit mehr Platz (und weg vom Auto) vorbeifahren
        ahead = self._car_ahead()
        if ahead:
            if self.overtake_frames == 0:
                forward, lateral, _ = ahead
                side = -1 if lateral > 4 else 1 if lateral < -4 else (1 if right >= left else -1)
                room = right if side == 1 else left
                if room < OVERTAKE_RANGE / 2:  # auf dieser Seite zu eng: andere Seite
                    side = -side
                self.overtake_side = side
            self.overtake_frames = OVERTAKE_HOLD
        elif self.overtake_frames > 0:
            self.overtake_frames -= 1
        if self.overtake_frames == 0:
            self.overtake_side = 0

        # Lenken: Richtung mit mehr Platz (lane_bias verschiebt die Wunschspur)
        # Überholt wird nur auf Geraden und nicht zur Strassenkante hin (in Kurven zieht der Überholschub sonst nach aussen)
        overtake_push = self.overtake_side * OVERTAKE_PUSH
        if (front < OVERTAKE_MIN_FRONT
                or (overtake_push > 0 and right < WALL_MARGIN)
                or (overtake_push < 0 and left < WALL_MARGIN)):
            overtake_push = 0
        diff = right - left + self.lane_bias + overtake_push + self._avoid_push(left, right)
        if diff > STEER_TOLERANCE:
            self.car.delta_view_angle = constant.STEERINGVALUE
        elif diff < -STEER_TOLERANCE:
            self.car.delta_view_angle = -constant.STEERINGVALUE
        else:
            self.car.delta_view_angle = 0

        # Seltener kleiner Fahrfehler: kurz in eine zufällige Richtung lenken
        if self.mistake_frames > 0:
            self.mistake_frames -= 1
            self.car.delta_view_angle = self.mistake_steer
        elif random.random() < MISTAKE_CHANCE * self.variation:
            self.mistake_frames = random.randint(2, 4)
            self.mistake_steer = random.choice((-1, 1)) * constant.STEERINGVALUE

        # Tempo: Wunschtempo wächst mit der freien Strasse geradeaus (Autos zählen nicht), plus etwas Rauschen
        target = (MIN_SPEED + (constant.MAXSPEED * self.car.topspeed_factor - MIN_SPEED)
                  * self.distance(track, 0, SPEED_LOOKAHEAD) / SPEED_LOOKAHEAD) * self.boldness
        target *= random.uniform(1 - 0.05 * self.variation, 1 + 0.05 * self.variation)
        if ahead and ahead[0] < CAR_BRAKE_DISTANCE and abs(ahead[1]) < 12:
            target = min(target, max(ahead[2].speed, 0))  # Auffahren vermeiden, solange noch kein Platz zum Vorbeifahren
        if front == 0 and left == 0 and right == 0:
            target = 0  # keine Strasse in Sicht (z. B. Streckenende): anhalten
        if self.car.speed > target:
            self.car.delta_speed = -constant.ACCELERATIONVALUE
        else:
            self.car.delta_speed = constant.ACCELERATIONVALUE
