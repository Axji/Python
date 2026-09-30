"""Einfaches Jump-and-Run mit pygame.

Steuerung: Pfeil links/rechts bewegt die Figur, die Leertaste springt. Wird die Leertaste mitten im Sprung
losgelassen und erneut gedrückt, ist ein Doppelsprung möglich.
"""
import sys
import pygame

# Pygame initialisieren
pygame.init()

# Fenstergrösse (Breite, Höhe) in Pixeln
window_size = (800, 600)

floor_height = 400  # y-Position des Bodens


# Fenster erstellen
screen = pygame.display.set_mode(window_size)

# Fenstertitel setzen
pygame.display.set_caption('Jump and Run')

# Uhr zur Steuerung der Bildrate
clock = pygame.time.Clock()

# Spielfigur laden
player_image = pygame.image.load('player.png')
player_rect = player_image.get_rect()

# Startposition der Figur
player_rect.x = 100
player_rect.y = floor_height
# Exakte (Float-)Position in y: Rect speichert nur ganze Zahlen, das würde beim Springen abdriften
player_y = float(floor_height)

# Laufgeschwindigkeit der Figur (Pixel pro Bild)
player_speed = 5

# Schwerkraft: Abnahme der Sprunggeschwindigkeit pro Bild
gravity = 0.5

# Anfangsgeschwindigkeit beim Absprung
jump_strength = 10
# Sprungzustand der Figur
is_jumping = False         # Figur ist in der Luft
double_jump = False         # Doppelsprung wurde in diesem Sprung schon benutzt
double_jump_ready = False   # Leertaste wurde in der Luft losgelassen, Doppelsprung ist möglich


# Aktuelle Sprunggeschwindigkeit (positiv = aufwärts)
jump_velocity = 0

# Hauptschleife des Spiels
while True:
    # Ereignisse verarbeiten (Fenster schliessen)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Gedrückte Tasten abfragen
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        # Figur nach links bewegen
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT]:
        # Figur nach rechts bewegen
        player_rect.x += player_speed
    if keys[pygame.K_SPACE]:
        # Sprung starten
        if not is_jumping:
            is_jumping = True
            jump_velocity = jump_strength
        # Schon in der Luft: ist ein Doppelsprung möglich?
        else:
            if not double_jump and double_jump_ready:
                double_jump = True
                jump_velocity = jump_strength
    else:
        # Sprungtaste während des Sprungs losgelassen => Doppelsprung wird möglich
        if is_jumping and not double_jump:
            double_jump_ready = True

    # Spieler im sichtbaren Bereich halten
    player_rect.x = max(0, min(window_size[0] - player_rect.width, player_rect.x))

    # Position anhand der Schwerkraft aktualisieren
    if is_jumping:
        player_y -= jump_velocity
        jump_velocity -= gravity
        if player_y >= floor_height:
            # Die Figur ist gelandet: Sprungzustand zurücksetzen
            is_jumping = False
            double_jump = False
            double_jump_ready = False
            player_y = float(floor_height)
        player_rect.y = round(player_y)

    # Figur zeichnen
    screen.fill((0, 0, 0))
    screen.blit(player_image, player_rect)

    # Bildschirm aktualisieren
    pygame.display.flip()

    # Bildrate auf 60 Bilder pro Sekunde begrenzen
    clock.tick(60)