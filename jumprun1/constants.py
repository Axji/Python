"""Zahlenwerte für das Jump-and-Run: Fenster, Physik und Spielregeln.

Alle Längen sind Pixel der kleinen Spielfläche (320 x 180). Sie wird beim Zeichnen vergrössert, das ergibt den
pixeligen Look. Geschwindigkeiten gelten pro Bild (bei 60 Bildern pro Sekunde).
"""

# Fenster
TILE = 16            # Kantenlänge eines Kachelfelds
SCREEN_W = 320       # Breite der Spielfläche
SCREEN_H = 180       # Höhe der Spielfläche
SCALE = 4            # Vergrösserung auf den Bildschirm (320 x 4 = 1280 Pixel Breite)
FPS = 60

# Bewegung der Spielfigur
GRAVITY = 0.35           # Zunahme der Fallgeschwindigkeit pro Bild
MAX_FALL = 6.0           # schnellster Fall
RUN_ACCEL = 0.25         # Beschleunigung am Boden
RUN_MAX = 1.8            # Höchstgeschwindigkeit beim Laufen
FRICTION = 0.2           # Abbremsen am Boden ohne Tastendruck
AIR_CONTROL = 0.7        # In der Luft lässt sich nur mit 70 % der Beschleunigung steuern
JUMP_SPEED = 6.2         # Startgeschwindigkeit des Sprungs (ergibt rund 55 Pixel Höhe)
JUMP_RELEASE_SPEED = 2.0  # Taste loslassen: Aufwärtstempo wird auf diesen Wert gekappt (kurzer Sprung)
COYOTE_FRAMES = 6        # Sprung ist noch kurz nach dem Verlassen der Kante möglich
JUMP_BUFFER_FRAMES = 6   # Sprung wird gemerkt, wenn die Taste kurz vor der Landung gedrückt wird

# Schiessen
BULLET_SPEED = 4.0       # immer waagrecht nach vorne
BULLET_LIFETIME = 90     # Bilder, danach verschwindet die Kugel
SHOOT_COOLDOWN = 18      # Mindestabstand zwischen zwei Schüssen in Bildern
MAX_BULLETS = 3          # so viele Kugeln dürfen gleichzeitig fliegen

# Gegner
ENEMY_SPEED = 0.5
ENEMY_STOMP_BOUNCE = 4.5  # Rückstoss nach oben, wenn man auf einen Gegner springt

# Spielregeln
START_LIVES = 3
INVULNERABLE_FRAMES = 90  # Schutzzeit nach einem Treffer (die Figur blinkt)
SCORE_COIN = 10
SCORE_SHOT = 100
SCORE_STOMP = 200
