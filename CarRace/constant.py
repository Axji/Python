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

COLLISION_SPEED_FACTOR = 0.4  # Beide Autos behalten bei einem Zusammenstoss diesen Anteil ihres Tempos

# Beschleunigung nimmt ab 80 % des Höchsttempos ab, damit die Höchstgeschwindigkeit schwerer zu erreichen ist
ACCEL_FALLOFF_START = 0.8  # Anteil des Höchsttempos, ab dem die Beschleunigung abnimmt
ACCEL_FALLOFF_MIN = 0.1    # Anteil der Beschleunigung, der beim Höchsttempo noch übrig ist

# Lenkwiderstand: Lenken kostet Tempo, anfangs wenig, je länger am Stück in eine Richtung gelenkt wird, desto mehr.
# Der Verlust ist ein Anteil des Tempos pro Bild; bei Dauerlenken pendelt sich das Tempo bei etwa
# ACCELERATIONVALUE / STEER_DRAG_MAX ein (enger Bogen = langsam).
STEER_DRAG_BASE = 0.004    # Tempoverlust-Anteil pro Bild beim Lenken (bei vollem Lenkeinschlag)
STEER_DRAG_GROWTH = 0.002  # Zusätzlicher Anteil pro Bild, das schon am Stück gelenkt wird
STEER_DRAG_MAX = 0.07      # Obergrenze des Verlust-Anteils pro Bild
STEER_RECOVERY = 2         # So viele Lenk-Bilder werden pro Bild ohne Lenken wieder "vergessen"

# Aufholjagd: Autos weit hinter dem Führenden bekommen ein höheres Tempolimit
CATCHUP_MAX_BOOST = 0.5     # Zusätzliches Tempolimit (0.5 = bis zu 50 % schneller)
CATCHUP_MIN_GAP = 40        # Rückstand in Pixeln, ab dem der Bonus beginnt
CATCHUP_FULL_GAP = 300      # Rückstand in Pixeln, ab dem der volle Bonus gilt
CATCHUP_DECAY_SECONDS = 1.5 # So lange sinkt der Bonus auf 0, wenn das Auto nicht mehr hinten liegt

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

