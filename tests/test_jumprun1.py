"""Tests für das Jump-and-Run (ohne Fenster: pygame läuft mit dem Dummy-Treiber)."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from jumprun1.constants import JUMP_SPEED, MAX_BULLETS, TILE  # noqa: E402
from jumprun1.entities import Bullet, Enemy, Player  # noqa: E402
from jumprun1.level import LEVEL_HEIGHT, LEVEL_WIDTH, Level  # noqa: E402
from jumprun1.pixelart import PLAYER_BODY, PLAYER_LEGS, PlayerSprites, from_ascii  # noqa: E402


def settled_player(level):
    """Stellt die Figur an den Start und lässt sie landen."""
    player = Player(*level.player_start)
    for _ in range(30):
        player.update(level, False, False, False)
    return player


def test_level_has_start_goal_and_objects():
    level = Level()
    assert len(level.grid) == LEVEL_HEIGHT
    assert all(len(row) == LEVEL_WIDTH for row in level.grid)
    assert level.flag_rect.width > 0
    assert level.enemy_starts and level.coins


def test_level_borders_are_walls_and_bottom_is_open():
    level = Level()
    assert level.is_solid(-1, 3)
    assert level.is_solid(LEVEL_WIDTH, 3)
    assert not level.is_solid(5, LEVEL_HEIGHT + 2)


def test_player_lands_on_ground():
    level = Level()
    player = settled_player(level)
    assert player.on_ground


def test_player_runs_forward_and_is_blocked_by_wall():
    level = Level()
    player = settled_player(level)
    start_x = player.rect.x
    for _ in range(20):
        player.update(level, False, True, False)
    assert player.rect.x > start_x
    assert player.facing == 1

    for _ in range(600):  # lange nach rechts laufen: die Figur bleibt im Spielplan
        player.update(level, False, True, False)
    assert player.rect.x < level.width


def test_jump_leaves_ground_and_is_variable():
    level = Level()
    high = settled_player(level)
    high.request_jump()
    high_top = high.rect.y
    for _ in range(60):
        high.update(level, False, False, True)
        high_top = min(high_top, high.rect.y)

    low = settled_player(level)
    low.request_jump()
    low_top = low.rect.y
    for _ in range(60):
        low.update(level, False, False, False)  # Taste sofort losgelassen
        low_top = min(low_top, low.rect.y)

    assert high_top < low_top
    assert settled_player(level).rect.y - high_top < JUMP_SPEED**2 / 0.7 + 2


def test_jump_buffer_and_coyote_time():
    level = Level()
    player = settled_player(level)
    player.on_ground = False  # gerade erst die Kante verlassen
    player.coyote = 3
    player.request_jump()
    player.update(level, False, False, True)
    assert player.vel.y < 0


def test_shoot_goes_straight_in_facing_direction():
    level = Level()
    player = settled_player(level)
    bullets = []
    player.facing = -1
    bullet = player.try_shoot(bullets)
    assert bullet.direction == -1
    start_y = bullet.rect.y
    for _ in range(5):
        bullet.update(level)
    assert bullet.rect.y == start_y  # keine Flugkurve
    assert bullet.rect.x < player.rect.x


def test_shoot_cooldown_and_bullet_limit():
    level = Level()
    player = settled_player(level)
    bullets = []
    assert player.try_shoot(bullets)
    assert player.try_shoot(bullets) is None  # Pause
    player.shoot_cooldown = 0
    bullets.extend([object()] * MAX_BULLETS)
    assert player.try_shoot(bullets) is None  # zu viele Kugeln unterwegs


def test_bullet_stops_at_wall():
    level = Level()
    bullet = Bullet(31 * TILE - 20, 8 * TILE + 8 + (180 - LEVEL_HEIGHT * TILE), 1)
    for _ in range(40):
        bullet.update(level)
    assert not bullet.alive


def test_enemy_turns_at_wall_and_does_not_fall_into_gap():
    level = Level()
    enemy = Enemy(*level.enemy_starts[0])
    for _ in range(2000):
        enemy.update(level)
    assert enemy.rect.top < level.height  # nicht in ein Loch gefallen


def test_sprite_rows_have_equal_width():
    widths = {len(row) for row in PLAYER_BODY}
    assert widths == {12}
    for legs in PLAYER_LEGS.values():
        assert {len(row) for row in legs} == {12}
    sprites = PlayerSprites()
    assert sprites.get(1, "idle").get_size() == (12, 16)
    assert sprites.get(-1, "jump").get_size() == (12, 16)


def test_from_ascii_rejects_ragged_rows():
    with pytest.raises(ValueError):
        from_ascii(["..", "..."])


def test_standing_player_stays_on_ground_without_flicker():
    level = Level()
    player = settled_player(level)
    for _ in range(60):
        player.update(level, False, False, False)
        assert player.on_ground
        assert player.sprite_state == "idle"


def test_running_player_never_shows_jump_frame_on_ground():
    level = Level()
    player = settled_player(level)
    for _ in range(40):
        player.update(level, False, True, False)
        assert player.sprite_state in ("run1", "run2", "idle")


def press_jump_in_air(player, level, frames_before):
    """Lässt die Figur `frames_before` Bilder fliegen und drückt dann Sprung."""
    for _ in range(frames_before):
        player.update(level, False, False, True)
    player.request_jump()
    player.update(level, False, False, True)


def test_double_jump_gives_second_boost_in_the_air():
    level = Level()
    player = settled_player(level)
    player.request_jump()
    player.update(level, False, False, True)
    assert player.vel.y < 0
    for _ in range(25):  # höchster Punkt ist überschritten, die Figur fällt
        player.update(level, False, False, True)
    assert player.vel.y > 0
    falling = player.vel.y
    press_jump_in_air(player, level, 0)
    assert player.vel.y < falling  # zweiter Sprung hat sie wieder nach oben geschoben
    assert player.jumps_used == 2


def test_no_third_jump_before_landing():
    level = Level()
    player = settled_player(level)
    for _ in range(2):  # zwei Sprünge hintereinander
        player.request_jump()
        player.update(level, False, False, True)
        for _ in range(8):
            player.update(level, False, False, True)
    assert player.jumps_used == 2
    assert not player.on_ground
    player.vel.y = 3.0  # fällt
    player.request_jump()
    player.update(level, False, False, True)
    assert player.vel.y > 3.0  # kein dritter Sprung, nur Schwerkraft


def test_landing_restores_both_jumps():
    level = Level()
    player = settled_player(level)
    player.jumps_used = 2
    player.update(level, False, False, False)  # steht auf dem Boden
    assert player.on_ground
    player.update(level, False, False, False)
    assert player.jumps_used == 0


def test_falling_off_a_ledge_leaves_only_one_air_jump():
    level = Level()
    player = settled_player(level)
    player.pos.y -= 60  # in der Luft, als wäre sie von einer Kante gefallen (ohne zu springen)
    player.rect.y = round(player.pos.y)
    player.on_ground = False
    player.coyote = 0
    player.jumps_used = 0
    player.vel.y = 1.0
    player.update(level, False, False, True)
    assert player.jumps_used == 1  # der Sprung vom Boden ist verfallen
    player.request_jump()
    player.update(level, False, False, True)
    assert player.jumps_used == 2  # ein Luftsprung ist noch möglich
    player.vel.y = 3.0
    player.request_jump()
    player.update(level, False, False, True)
    assert player.vel.y > 3.0  # weiter geht es nicht


def test_goal_zone_reaches_above_the_flag():
    level = Level()
    assert level.goal_rect.top < level.flag_rect.top  # man kann das Ziel nicht überspringen
    assert level.goal_rect.bottom >= level.flag_rect.bottom
    assert level.goal_rect.x == level.flag_rect.x
