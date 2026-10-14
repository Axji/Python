"""Spielschleife, Regeln (Münzen, Gegner, Leben, Ziel), Kamera und Zeichnen."""
import math

import pygame

from .constants import (
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
from .entities import Enemy, Player
from .level import Y_OFFSET, Level
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
        self.font = pygame.font.Font(None, 16)
        self.big_font = pygame.font.Font(None, 28)

        self.background = Background()
        self.tiles = make_tiles()
        self.player_sprites = PlayerSprites()
        self.enemy_images = enemy_frames()
        self.coin_image = coin_sprite()
        self.bullet_images = bullet_sprites()
        self.flag_image = flag_sprite()
        self.reset()

    def reset(self):
        """Startet das Spiel von vorne."""
        self.level = Level()
        self.player = Player(*self.level.player_start)
        self.enemies = [Enemy(x, y) for x, y in self.level.enemy_starts]
        self.coins = [coin.copy() for coin in self.level.coins]
        self.bullets = []
        self.score = 0
        self.lives = START_LIVES
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
                if self.state != PLAYING and event.key in (pygame.K_r, pygame.K_RETURN):
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
        self.collect_coins()
        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive and e.rect.top < self.level.height + 64]

        if self.player.rect.colliderect(self.level.flag_rect):
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
        self.draw_hud()
        if self.state != PLAYING:
            self.draw_message()
        pygame.transform.scale(self.canvas, self.window.get_size(), self.window)  # ohne Glättung = pixelig
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
                    image = self.tiles["brick" if char == "B" else "block"]
                self.canvas.blit(image, (col * TILE - cam, row * TILE + Y_OFFSET))

    def draw_objects(self, cam):
        flag = self.level.flag_rect
        self.canvas.blit(self.flag_image, (flag.x - cam, flag.y))

        for coin in self.coins:
            bob = round(math.sin((self.ticks + coin.x) / 10) * 1.5)  # Münzen schweben leicht auf und ab
            self.canvas.blit(self.coin_image, (coin.x - cam, coin.y + bob))
        for enemy in self.enemies:
            self.canvas.blit(self.enemy_images[enemy.frame], (enemy.rect.x - cam, enemy.rect.y))
        for bullet in self.bullets:
            self.canvas.blit(self.bullet_images[bullet.direction], (bullet.rect.x - cam, bullet.rect.y))

        player = self.player
        blinking = player.invulnerable and (player.invulnerable // 4) % 2 == 0
        if not blinking:
            image = self.player_sprites.get(player.facing, player.sprite_state)
            self.canvas.blit(image, (player.rect.x - cam, player.rect.y))

    def draw_text(self, font, text, x, y, color=(255, 255, 255), center=False):
        shadow = font.render(text, False, (30, 30, 50))
        image = font.render(text, False, color)
        if center:
            x -= image.get_width() // 2
        self.canvas.blit(shadow, (x + 1, y + 1))
        self.canvas.blit(image, (x, y))

    def draw_hud(self):
        self.draw_text(self.font, f"PUNKTE {self.score:05d}", 6, 5)
        self.draw_text(self.font, f"LEBEN {max(self.lives, 0)}", SCREEN_W - 56, 5)

    def draw_message(self):
        title = "GESCHAFFT!" if self.state == WON else "GAME OVER"
        color = (252, 214, 50) if self.state == WON else (240, 80, 80)
        self.draw_text(self.big_font, title, SCREEN_W // 2, 60, color, center=True)
        self.draw_text(self.font, f"PUNKTE {self.score}", SCREEN_W // 2, 88, center=True)
        self.draw_text(self.font, "R = NOCHMAL    ESC = ENDE", SCREEN_W // 2, 104, center=True)
