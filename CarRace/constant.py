"""Konstanten für das Autorennen (Fenster, Auto, Physik und Streckenfarben)."""

# Fenstergrösse in Pixeln (Breite / Höhe)
WINDOWWITH = 1440
WINDOWHIGH = 880


# Grösse des Autos in Pixeln
PLAYERHIGH =20
PLAYERWITH =20

MAXSPEED = 10          # Höchstgeschwindigkeit vorwärts
MAXSPEED_REVERSE = 5   # Höchstgeschwindigkeit rückwärts
MALUSFACTOR = 0.3      # Faktor auf die Höchstgeschwindigkeit, wenn das Auto neben der Strasse fährt

MAXANGLE = 4 / 8  # Maximaler Lenkwinkel (im Code aktuell nicht verwendet)

# Startposition des Autos auf der Strecke
STARTPOSX = 100.0
STARTPOSY = 165.0

ACCELERATIONVALUE = 0.25  # Geschwindigkeitsänderung pro Bild, solange Gas oder Bremse gedrückt ist
STEERINGVALUE = 5         # Drehung in Grad pro Bild, solange eine Lenktaste gedrückt ist


# Farben (RGBA) der Streckenbilder; werden zur Bodenerkennung verglichen
COLOR_STREET = (100, 100, 100, 255)
COLOR_FENCE  = (255, 5, 5, 255)
COLOR_FINISH = (255, 255, 5, 255)

