"""Spielschleife, Regeln (Münzen, Gegner, Leben, Ziel), Kamera und Zeichnen."""
import math
import random

import pygame

from .constants import (
    BLOCK_BUMP_FRAMES,
    ENEMY_STOMP_BOUNCE,
    FPS,
    SCALE,
    SCORE_COIN,
    SCORE_SHOT,
    SCORE_STOMP,
    SCREEN_H,
    SCREEN_W,
    START_LIVES,
    TILE,
)
from .entities import CoinPop, Enemy, Player
from .level import Y_OFFSET, Level
from .levelgen import generate_grid
from .pixelart import Background, PlayerSprites, bullet_sprites, coin_sprite, enemy_frames, flag_sprite, make_tiles

LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
SHOOT_KEYS = (pygame.K_x, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_j)

PLAYING, WON, GAME_OVER = "playing", "won", "game over"


class Game:
    """Hält alle Teile des Spiels zusammen. `run()` startet die Schleife."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Jump and Run")
        self.window = pygame.display.set_mode((SCREEN_W * SCALE, SCREEN_H * SCALE))
        self.canvas = pygame.Surface((SCREEN_W, SCREEN_H))  # hier wird klein gezeichnet, dann vergrössert
        self.clock = pygame.time.Clock()
        # Schrift wird erst nach dem Vergrössern in voller Fensterauflösung gezeichnet: glatt und gut lesbar
        self.font = self.load_font(7 * SCALE)
        self.big_font = self.load_font(18 * SCALE)

        self.background = Background()
        self.tiles = make_tiles()
        self.player_sprites = PlayerSprites()
        self.enemy_images = enemy_frames()
        self.coin_image = coin_sprite()
        self.bullet_images = bullet_sprites()
        self.flag_image = flag_sprite()
        self.reset()

    def reset(self):
        """Startet das Spiel von vorne: Level 1, neue Punkte und Leben, neuer Zufallswert für die späteren Level."""
        self.seed = random.randrange(1_000_000)
        self.score = 0
        self.lives = START_LIVES
        self.start_level(1)

    def next_level(self):
        """Weiter zum nächsten, frisch erzeugten Level. Punkte und Leben bleiben."""
        self.start_level(self.level_number + 1)

    def start_level(self, number):
        """Baut Level `number` auf: das erste ist von Hand gebaut, alle weiteren kommen aus dem Level-Generator."""
        self.level_number = number
        self.level = Level() if number == 1 else Level(generate_grid(self.seed, number))
        self.player = Player(*self.level.player_start)
        self.enemies = [Enemy(x, y) for x, y in self.level.enemy_starts]
        self.coins = [coin.copy() for coin in self.level.coins]
        self.bullets = []
        self.coin_pops = []   # Münzen, die gerade aus einem Block springen
        self.bumps = {}       # (Spalte, Zeile) eines getroffenen Blocks -> Restzeit seines Hüpfers
        self.state = PLAYING
        self.camera_x = 0
        self.ticks = 0

    # ---------------------------------------------------------------- Eingabe und Ablauf

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        """Verarbeitet Tastendrücke. Gibt False zurück, wenn das Spiel beendet werden soll."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if self.state == WON and event.key in (pygame.K_r, pygame.K_RETURN):
                    self.next_level()
                elif self.state != PLAYING and event.key in (pygame.K_r, pygame.K_RETURN):
                    self.reset()
                elif event.key in JUMP_KEYS:
                    self.player.request_jump()
                elif event.key in SHOOT_KEYS:
                    self.shoot()
        return True

    def shoot(self):
        bullet = self.player.try_shoot(self.bullets)
        if bullet:
            self.bullets.append(bullet)

    def update(self):
        if self.state != PLAYING:
            return
        self.ticks += 1
        keys = pygame.key.get_pressed()
        left = any(keys[k] for k in LEFT_KEYS)
        right = any(keys[k] for k in RIGHT_KEYS)
        jump_held = any(keys[k] for k in JUMP_KEYS)
        if any(keys[k] for k in SHOOT_KEYS):
            self.shoot()  # Taste gedrückt halten = Dauerfeuer (mit Pause zwischen den Schüssen)

        self.player.update(self.level, left, right, jump_held)
        for bullet in self.bullets:
            bullet.update(self.level)
        for enemy in self.enemies:
            enemy.update(self.level)

        self.check_bullet_hits()
        self.check_enemy_contact()
        self.hit_blocks()
        self.collect_coins()
        self.update_block_effects()
        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive and e.rect.top < self.level.height + 64]

        if self.player.rect.colliderect(self.level.goal_rect):
            self.state = WON
        if self.player.rect.top > self.level.height + 32:
            self.lose_life(respawn=True)
        self.update_camera()

    def check_bullet_hits(self):
        for bullet in self.bullets:
            for enemy in self.enemies:
                if bullet.alive and enemy.alive and bullet.rect.colliderect(enemy.rect):
                    bullet.alive = enemy.alive = False
                    self.score += SCORE_SHOT

    def check_enemy_contact(self):
        player = self.player
        for enemy in self.enemies:
            if not enemy.alive or not player.rect.colliderect(enemy.rect):
                continue
            stomping = player.vel.y > 0 and player.rect.bottom - enemy.rect.top <= 8
            if stomping:  # von oben draufgesprungen
                enemy.alive = False
                player.vel.y = -ENEMY_STOMP_BOUNCE
                self.score += SCORE_STOMP
            elif not player.invulnerable:
                player.hurt(enemy.rect.centerx)
                self.lose_life(respawn=False)

    def collect_coins(self):
        for coin in self.coins[:]:
            if self.player.rect.colliderect(coin):
                self.coins.remove(coin)
                self.score += SCORE_COIN

    def hit_blocks(self):
        """Stösst die Figur beim Springen von unten an einen Fragezeichen-Block, fällt eine Münze heraus.

        Berührt der Kopf zwei Blöcke gleichzeitig, zählt der, der mehr unter der Figur liegt.
        """
        tiles = self.player.ceiling_tiles
        if not tiles:
            return
        player_rect = self.player.rect
        tile = max(tiles, key=lambda t: min(t.right, player_rect.right) - max(t.left, player_rect.left))
        col, row = self.level.tile_of(tile)
        if self.level.hit_block(col, row):
            self.score += SCORE_COIN
            self.bumps[(col, row)] = BLOCK_BUMP_FRAMES
            self.coin_pops.append(CoinPop(tile.x + TILE // 2 - 4, tile.y - 8))

    def update_block_effects(self):
        """Lässt Block-Hüpfer und fliegende Münzen ablaufen."""
        self.bumps = {pos: left - 1 for pos, left in self.bumps.items() if left > 1}
        for pop in self.coin_pops:
            pop.update()
        self.coin_pops = [pop for pop in self.coin_pops if pop.alive]

    def lose_life(self, respawn):
        self.lives -= 1
        if self.lives <= 0:
            self.state = GAME_OVER
        elif respawn:
            self.player.respawn(*self.level.player_start)

    def update_camera(self):
        """Die Kamera folgt der Figur, bleibt aber innerhalb des Spielplans."""
        target = self.player.rect.centerx - SCREEN_W // 2
        self.camera_x = max(0, min(target, self.level.width - SCREEN_W))

    # ---------------------------------------------------------------- Zeichnen

    def draw(self):
        cam = int(self.camera_x)
        self.background.draw(self.canvas, cam)
        self.draw_tiles(cam)
        self.draw_objects(cam)
        pygame.transform.scale(self.canvas, self.window.get_size(), self.window)  # ohne Glättung = pixelig
        self.draw_hud()  # Text kommt erst danach, damit er nicht mit vergrössert und verpixelt wird
        if self.state != PLAYING:
            self.draw_message()
        pygame.display.flip()

    def draw_tiles(self, cam):
        first = cam // TILE
        for row in range(len(self.level.grid)):
            for col in range(first, first + SCREEN_W // TILE + 2):
                char = self.level.char_at(col, row)
                if char == ".":
                    continue
                if char == "#":
                    open_above = not self.level.is_solid(col, row - 1)
                    image = self.tiles["grass" if open_above else "dirt"]
                else:
                    image = self.tiles[{"B": "brick", "?": "block", "U": "used"}[char]]
                bump = self.bumps.get((col, row), 0)
                lift = round(math.sin(bump / BLOCK_BUMP_FRAMES * math.pi) * 4)  # getroffener Block hüpft kurz nach oben
                self.canvas.blit(image, (col * TILE - cam, row * TILE + Y_OFFSET - lift))

    def draw_objects(self, cam):
        flag = self.level.flag_rect
        self.canvas.blit(self.flag_image, (flag.x - cam, flag.y))

        for coin in self.coins:
            bob = round(math.sin((self.ticks + coin.x) / 10) * 1.5)  # Münzen schweben leicht auf und ab
            self.canvas.blit(self.coin_image, (coin.x - cam, coin.y + bob))
        for pop in self.coin_pops:  # Münzen, die gerade aus einem Block springen
            self.canvas.blit(self.coin_image, (round(pop.pos.x) - cam, round(pop.pos.y)))
        for enemy in self.enemies:
            self.canvas.blit(self.enemy_images[enemy.frame], (enemy.rect.x - cam, enemy.rect.y))
        for bullet in self.bullets:
            self.canvas.blit(self.bullet_images[bullet.direction], (bullet.rect.x - cam, bullet.rect.y))

        player = self.player
        blinking = player.invulnerable and (player.invulnerable // 4) % 2 == 0
        if not blinking:
            image = self.player_sprites.get(player.facing, player.sprite_state)
            self.canvas.blit(image, (player.rect.x - cam, player.rect.y))

    @staticmethod
    def load_font(size):
        """Glatte, gut lesbare Systemschrift (fett). Fehlt sie, nimmt pygame seine Standardschrift."""
        return pygame.font.SysFont("segoeui,arial,verdana,dejavusans", size, bold=True)

    def draw_text(self, font, text, x, y, color=(255, 255, 255), align="left"):
        """Zeichnet Text mit dunklem Schatten direkt ins Fenster. x und y sind Punkte der kleinen Spielfläche."""
        image = font.render(text, True, color)  # True = geglättete Kanten
        shadow = font.render(text, True, (20, 24, 48))
        px, py = x * SCALE, y * SCALE
        if align == "center":
            px -= image.get_width() // 2
        elif align == "right":
            px -= image.get_width()
        self.window.blit(shadow, (px + 2, py + 2))
        self.window.blit(image, (px, py))

    def draw_hud(self):
        self.draw_text(self.font, f"PUNKTE  {self.score:05d}", 6, 2)
        self.draw_text(self.font, f"LEVEL  {self.level_number}", SCREEN_W // 2, 2, align="center")
        self.draw_text(self.font, f"LEBEN  {max(self.lives, 0)}", SCREEN_W - 6, 2, align="right")

    def draw_message(self):
        title = f"LEVEL {self.level_number} GESCHAFFT!" if self.state == WON else "GAME OVER"
        color = (252, 214, 50) if self.state == WON else (240, 80, 80)
        self.draw_text(self.big_font, title, SCREEN_W // 2, 50, color, align="center")
        self.draw_text(self.font, f"PUNKTE  {self.score}", SCREEN_W // 2, 88, align="center")
        hint = "Enter = Nächstes Level      Esc = Ende" if self.state == WON else "R = Nochmal      Esc = Ende"
        self.draw_text(self.font, hint, SCREEN_W // 2, 104, align="center")
