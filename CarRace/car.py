"""Das Auto des Rennspiels: Zustand (Position, Tempo, Blickwinkel) und Steuerung."""
import constant
import math
import pygame

def recolor(image, color):
    """Färbt die bunten Pixel des Autobildes in `color` um; Helligkeit, Schwarz/Weiss und Transparenz bleiben."""
    image = image.copy()
    for x in range(image.get_width()):
        for y in range(image.get_height()):
            r, g, b, a = image.get_at((x, y))
            if a and max(r, g, b) - min(r, g, b) > 60:
                shade = max(r, g, b) / 255
                image.set_at((x, y), (int(color[0] * shade), int(color[1] * shade), int(color[2] * shade), a))
    return image


class Car:
    """Ein Auto mit Position, Geschwindigkeit und Fahrtrichtung.

    Die `delta_*`-Werte sind die aktuell gedrückten Eingaben (Gas/Bremse bzw. Lenkung). `update()` wendet sie
    einmal pro Bild an.
    """
    pos_x = constant.STARTPOSX
    pos_y = constant.STARTPOSY
    speed = 0
    delta_speed = 0
    view_angle = 0
    delta_view_angle = 0
    name = ""
    distance_driven = 0  # Gesamte gefahrene Strecke in Pixeln (Mass für die Rennposition)
    topspeed_factor = 1  # Aufholbonus aufs Tempolimit (1 = normal)
    steer_direction = 0  # Richtung des laufenden Bogens (-1 links, 1 rechts)
    steer_frames = 0     # Wie lange (in Bildern) schon am Stück gelenkt wird; bestimmt den Lenkwiderstand
    is_neural = False    # True bei der lernenden KI (kollidiert nicht mit anderen KI-Autos)
    activeMalusFactor = 1  # 1 = normaler Boden, kleiner als 1 = Strafe (Tempolimit sinkt)

    def __init__(self, name, image, color=None):
        """Erstellt das Auto am Startpunkt. `image` ist der Dateiname des Autobildes, `color` (R, G, B) färbt es um."""
        self.speed = 0
        self.view_angle = 0
        self.pos_x = constant.STARTPOSX
        self.pos_y = constant.STARTPOSY
        self.name = name
        self.carImage = pygame.image.load(image)
        if color:
            self.carImage = recolor(self.carImage, color)
        self.distance_driven = 0
        self.steer_frames = 0
        self.steer_direction = 0
        self.topspeed_factor = 1
        self.delta_speed = 0
        self.delta_view_angle = 0
        self.activeMalusFactor = 1
        pass

    def reset(self):
        """Setzt Tempo, Richtung und Position auf den Start zurück (z. B. beim Streckenwechsel)."""
        self.speed = 0
        self.view_angle = 0
        self.pos_x = constant.STARTPOSX
        self.pos_y = constant.STARTPOSY
        self.distance_driven = 0
        self.steer_frames = 0
        self.steer_direction = 0
        self.topspeed_factor = 1
        pass

    def update(self):
        """Berechnet die neue Geschwindigkeit, Richtung und Position für das nächste Bild."""
        self.speed += self.effective_acceleration()
        self.apply_steering_drag()
        self.distance_driven += self.speed

        self.speedLimiter()

        self.view_angle += self.delta_view_angle

        # Bewegung in Blickrichtung: Kosinus liefert den Anteil in x, Sinus den Anteil in y
        self.pos_x += round(math.cos(
            math.radians(self.view_angle)) * self.speed)
        self.pos_y += round(math.sin(math.radians(self.view_angle)) * self.speed)
        pass

    def effective_acceleration(self):
        """`delta_speed`, aber Gas wird ab 80 % des Höchsttempos schwächer (beim Höchsttempo nur noch 10 %).

        Bremsen und Rückwärtsfahren sind nicht betroffen.
        """
        if self.delta_speed <= 0:
            return self.delta_speed
        top = constant.MAXSPEED * self.topspeed_factor
        start = constant.ACCEL_FALLOFF_START * top
        if self.speed <= start:
            return self.delta_speed
        share = min(1, (self.speed - start) / (top - start))  # 0 bei 80 %, 1 beim Höchsttempo
        return self.delta_speed * (1 - (1 - constant.ACCEL_FALLOFF_MIN) * share)

    def apply_steering_drag(self):
        """Lenken kostet Tempo: anfangs wenig, mit der Dauer des Lenkens in eine Richtung immer mehr.

        So muss man zwischen einem weiten Bogen mit hohem Tempo und einem engen Bogen mit Tempoverlust wählen.
        Ohne Lenken wird die "Lenkdauer" wieder abgebaut.
        """
        steer = min(1, abs(self.delta_view_angle) / constant.STEERINGVALUE)  # 0 = geradeaus, 1 = voller Einschlag
        if steer == 0:
            self.steer_frames = max(0, self.steer_frames - constant.STEER_RECOVERY)
            return
        direction = 1 if self.delta_view_angle > 0 else -1
        if direction != self.steer_direction:  # Richtungswechsel: neuer Bogen, Lenkdauer beginnt von vorn
            self.steer_frames = 0
            self.steer_direction = direction
        self.steer_frames += steer
        drag = min(constant.STEER_DRAG_MAX, constant.STEER_DRAG_BASE + constant.STEER_DRAG_GROWTH * self.steer_frames)
        self.speed *= 1 - drag * steer

    def topspeed_limit(self):
        """Aktuelles Tempolimit vorwärts: Höchstgeschwindigkeit mal Boden-Malus mal Aufholbonus."""
        return constant.MAXSPEED * self.activeMalusFactor * self.topspeed_factor

    def speedLimiter(self):
        """Begrenzt die Geschwindigkeit auf das Tempolimit vorwärts bzw. rückwärts (inkl. Malus)."""
        if self.speed > self.topspeed_limit():
            self.speed = self.topspeed_limit()
        if self.speed < (constant.MAXSPEED_REVERSE * -1 * self.activeMalusFactor):
            self.speed = (constant.MAXSPEED_REVERSE * -1 * self.activeMalusFactor)

    def accelerate(self):
        """Gas geben: erhöht die Beschleunigung. Wird beim Loslassen der Bremstaste ebenfalls verwendet."""
        self.delta_speed += constant.ACCELERATIONVALUE
        pass

    def brake(self):
        """Bremsen: verringert die Beschleunigung. Wird beim Loslassen der Gastaste ebenfalls verwendet."""
        self.delta_speed -= constant.ACCELERATIONVALUE
        pass

    def left(self):
        """Nach links lenken."""
        self.steering(-1); #steering mit passender Seite aufrufen -1 / 1 verändert nur dir richtung
        pass

    def right(self):
        """Nach rechts lenken."""
        self.steering(1) #steering mit passnder Seite aufrufen -1 / 1 verändert nur dir richtung
        pass

    def steering(self, side):
        """Ändert die Drehgeschwindigkeit: side = -1 (links) oder 1 (rechts)."""
        self.delta_view_angle += constant.STEERINGVALUE * side
        pass


    def getPosAsRect(self):
        """Liefert die Position als pygame-Rechteck zum Zeichnen."""
        rect = pygame.Rect(self.pos_x, self.pos_y, constant.PLAYERHIGH, constant.PLAYERWITH)
        return rect

    def getimage(self):
        """Liefert das Autobild passend zur Fahrtrichtung gedreht."""
        return pygame.transform.rotate(self.carImage, self.view_angle * -1) #Rotate winkel ist umgekehrt zu dem wie er in Game benutzt wird.

    def setmalus(self, malusfactor):
        """Setzt den Malus-Faktor je nach Untergrund (1 = Strasse, kleiner = Abseits)."""
        self.activeMalusFactor = float(malusfactor)
        pass



def center(car):
    """Mittelpunkt des Autos (x, y) in Pixeln."""
    return (car.pos_x + constant.PLAYERWITH / 2, car.pos_y + constant.PLAYERHIGH / 2)


def resolve_collision(a, b):
    """Prüft, ob sich die Autos a und b berühren (Kreise mit Durchmesser = Autogrösse).

    Bei einer Berührung werden sie auseinandergeschoben und beide verlieren Tempo.
    Gibt den Kollisionspunkt (x, y) zurück, sonst None.
    """
    ax, ay = center(a)
    bx, by = center(b)
    dx, dy = bx - ax, by - ay
    dist = math.hypot(dx, dy)
    min_dist = constant.PLAYERWITH
    if dist >= min_dist:
        return None
    if dist == 0:  # exakt übereinander: beliebige Richtung wählen
        dx, dy, dist = 1.0, 0.0, 1.0
    push = (min_dist - dist) / 2 + 1
    a.pos_x -= dx / dist * push
    a.pos_y -= dy / dist * push
    b.pos_x += dx / dist * push
    b.pos_y += dy / dist * push
    a.speed *= constant.COLLISION_SPEED_FACTOR
    b.speed *= constant.COLLISION_SPEED_FACTOR
    return ((ax + bx) / 2, (ay + by) / 2)


def update_catchup(cars, fps):
    """Aufholbonus: Autos weit hinter dem Führenden dürfen schneller fahren als normal.

    Der Bonus steigt sofort mit dem Rückstand, sinkt aber höchstens über CATCHUP_DECAY_SECONDS wieder auf normal
    (z. B. nachdem das Auto überholt hat).
    """
    leader = max(c.distance_driven for c in cars)
    decay = constant.CATCHUP_MAX_BOOST / (constant.CATCHUP_DECAY_SECONDS * fps)
    for c in cars:
        gap = leader - c.distance_driven
        part = (gap - constant.CATCHUP_MIN_GAP) / (constant.CATCHUP_FULL_GAP - constant.CATCHUP_MIN_GAP)
        target = 1 + constant.CATCHUP_MAX_BOOST * min(1, max(0, part))
        c.topspeed_factor = max(target, c.topspeed_factor - decay)
