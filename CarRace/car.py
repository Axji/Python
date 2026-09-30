"""Das Auto des Rennspiels: Zustand (Position, Tempo, Blickwinkel) und Steuerung."""
import constant
import math
import pygame

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
    activeMalusFactor = 1  # 1 = normaler Boden, kleiner als 1 = Strafe (Tempolimit sinkt)

    def __init__(self, name, image):
        """Erstellt das Auto am Startpunkt. `image` ist der Dateiname des Autobildes."""
        self.speed = 0
        self.view_angle = 0
        self.pos_x = constant.STARTPOSX
        self.pos_y = constant.STARTPOSY
        self.name = name
        self.carImage = pygame.image.load(image)
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
        pass

    def update(self):
        """Berechnet die neue Geschwindigkeit, Richtung und Position für das nächste Bild."""
        self.speed += self.delta_speed

        self.speedLimiter()

        self.view_angle += self.delta_view_angle

        # Bewegung in Blickrichtung: Kosinus liefert den Anteil in x, Sinus den Anteil in y
        self.pos_x += round(math.cos(
            math.radians(self.view_angle)) * self.speed)
        self.pos_y += round(math.sin(math.radians(self.view_angle)) * self.speed)
        pass

    def speedLimiter(self):
        """Begrenzt die Geschwindigkeit auf das Tempolimit vorwärts bzw. rückwärts (inkl. Malus)."""
        if self.speed > (constant.MAXSPEED * float(self.activeMalusFactor)):
            self.speed = (constant.MAXSPEED * float(self.activeMalusFactor))
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


