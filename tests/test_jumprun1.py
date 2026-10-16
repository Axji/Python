"""Tests für das Jump-and-Run (ohne Fenster: pygame läuft mit dem Dummy-Treiber)."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from jumprun1.constants import BLOCK_COINS, JUMP_SPEED, MAX_BULLETS, SCORE_COIN, TILE  # noqa: E402
from jumprun1.entities import Bullet, Enemy, Player  # noqa: E402
from jumprun1.game import Game  # noqa: E402
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


# ---------------------------------------------------------------- Fragezeichen-Blöcke


def test_question_block_gives_three_coins_then_becomes_empty():
    level = Level()
    col, row = next(iter(level.block_coins))
    for _ in range(3):
        assert level.char_at(col, row) == "?"
        assert level.hit_block(col, row)
    assert level.char_at(col, row) == "U"
    assert level.is_solid(col, row)  # der leere Block bleibt fest
    assert not level.hit_block(col, row)  # nichts mehr zu holen


def test_brick_gives_no_coin():
    level = Level()
    brick = next((c, r) for r, line in enumerate(level.grid) for c, ch in enumerate(line) if ch == "B")
    assert not level.hit_block(*brick)


class _Keys:
    """Ersatz für pygame.key.get_pressed(): nur die genannten Tasten sind gedrückt."""

    def __init__(self, *pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


def clean_game():
    """Spiel ohne Gegner und Bodenmünzen, damit nur die Block-Punkte zählen."""
    game = Game()
    game.enemies = []
    game.coins = []
    return game


def _jump_under(game, monkeypatch, col, row):
    """Stellt die Figur unter den Block (Spalte, Zeile), lässt sie springen und wartet, bis sie wieder steht."""
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: _Keys(pygame.K_SPACE))
    player = game.player
    ground_y = game.level.player_start[1]
    player.pos.update(col * TILE + 2, ground_y)
    player.rect.topleft = (col * TILE + 2, ground_y)
    player.vel.update(0, 0)
    for _ in range(5):
        game.update()
    player.request_jump()
    for _ in range(45):
        game.update()


def test_jumping_against_question_block_drops_coin_and_score(monkeypatch):
    game = clean_game()
    col, row = next(k for k in game.level.block_coins)
    _jump_under(game, monkeypatch, col, row)
    assert game.score == SCORE_COIN
    assert game.level.block_coins[(col, row)] == BLOCK_COINS - 1


def test_block_runs_empty_after_three_jumps(monkeypatch):
    game = clean_game()
    col, row = next(k for k in game.level.block_coins)
    for _ in range(4):
        _jump_under(game, monkeypatch, col, row)
    assert game.level.char_at(col, row) == "U"
    assert game.score == BLOCK_COINS * SCORE_COIN  # die vierte Berührung bringt nichts mehr


def test_jumping_against_brick_gives_nothing(monkeypatch):
    game = clean_game()
    brick_col = next(c for c in range(8, 12) if game.level.char_at(c, 6) == "B")
    _jump_under(game, monkeypatch, brick_col, 6)
    assert game.score == 0


# ---------------------------------------------------------------- Level-Generator (ab Level 2)

from jumprun1 import reach  # noqa: E402
from jumprun1.levelgen import DELAYED_GAPS, GENERATED_WIDTH, KINDS, REACH, generate_grid, plan, profile, required  # noqa: E402

SEEDS = range(40)


def test_generated_level_is_twice_as_long_as_level_one():
    assert GENERATED_WIDTH == 2 * LEVEL_WIDTH
    for seed in range(5):
        level = Level(generate_grid(seed, 2))
        assert level.cols == 2 * LEVEL_WIDTH
        assert level.width == 2 * Level().width
        assert len(level.grid) == LEVEL_HEIGHT
        assert level.flag_rect.width > 0 and level.enemy_starts and level.coins
        assert level.player_start[0] < level.flag_rect.x


def test_generator_is_deterministic_and_varies_with_seed():
    assert generate_grid(7, 2) == generate_grid(7, 2)
    assert generate_grid(7, 2) != generate_grid(8, 2)
    assert generate_grid(7, 2) != generate_grid(7, 3)


def test_generated_start_and_goal_stand_on_solid_ground():
    for seed in SEEDS:
        grid = generate_grid(seed, 2)
        assert sum(row.count("P") for row in grid) == 1
        assert sum(row.count("F") for row in grid) == 1
        row = next(r for r, line in enumerate(grid) if "P" in line)
        assert grid[row + 1][grid[row].index("P")] == "#"
        row = next(r for r, line in enumerate(grid) if "F" in line)
        assert grid[row + 1][grid[row].index("F")] == "#"


def test_no_gap_or_step_is_beyond_the_double_jump():
    for number in (2, 3, 5):
        for seed in SEEDS:
            for gap, rise in profile(generate_grid(seed, number)):
                assert rise in REACH, (seed, gap, rise)
                assert 0 <= gap <= REACH[rise][0][2], (seed, number, gap, rise)
                if gap == 0 and rise > 0:
                    assert REACH[rise][0][1] >= 0  # eine Mauer dieser Höhe lässt sich überhaupt erklimmen


def needs_double(step):
    """Geht dieses Hindernis nicht mit dem Einzelsprung (zu breit oder zu hoch)?"""
    return step.gap > REACH[step.rise][0][0]


def test_generated_levels_have_gaps_and_walls_a_single_jump_cannot_do():
    for number in (2, 3, 6):
        for seed in SEEDS:
            steps, _ = plan(seed, number)
            assert set(required(number)) <= {s.kind for s in steps}
            assert any(s.kind == "double_gap" and needs_double(s) for s in steps)
            assert any(s.kind == "wall_double" and needs_double(s) for s in steps)
            assert all(s.gap <= REACH[s.rise][0][2] for s in steps)
            assert any(not needs_double(s) for s in steps)  # und auch leichte Stellen
            if number >= 3:  # Drops mit verzögertem Doppelsprung
                assert any(s.kind == "delayed_drop" and s.rise < 0 and s.gap > REACH[s.rise][0][1] for s in steps)


def hard_share(number):
    steps = [s for seed in SEEDS for s in plan(seed, number)[0]]
    return sum(needs_double(s) for s in steps) / len(steps)


def test_level_two_is_mild_and_difficulty_rises_with_the_level():
    assert hard_share(2) < 0.4          # die Mehrheit geht mit dem Einzelsprung
    assert hard_share(2) > 0.1          # ein Teil braucht aber den Doppelsprung
    assert hard_share(2) < hard_share(5) < hard_share(10)


def average_gap(number):
    gaps = [s.gap for seed in SEEDS for s in plan(seed, number)[0] if s.kind in ("single_gap", "double_gap")]
    return sum(gaps) / len(gaps)


def test_gaps_get_wider_with_the_level():
    assert average_gap(2) < average_gap(10)


def test_generated_terrain_matches_the_plan():
    for seed in range(10):
        steps, _ = plan(seed, 2)
        found = profile(generate_grid(seed, 2))
        assert found[: len(steps)] == [(s.gap, s.rise) for s in steps]


def test_generated_level_has_no_blocks_near_platform_edges():
    """Ziegel und Blöcke hängen weit weg von den Kanten, damit sie keinen Absprung oder Sprung behindern."""
    for seed in SEEDS:
        grid = generate_grid(seed, 2)
        for r, line in enumerate(grid):
            for c, char in enumerate(line):
                if char in "B?":
                    ground = next(rr for rr in range(r, LEVEL_HEIGHT) if grid[rr][c] == "#")
                    for dc in range(-3, 4):
                        assert grid[ground][c + dc] == "#" and grid[ground - 1][c + dc] != "#", (seed, r, c)


@pytest.mark.parametrize("rise", sorted(REACH))
def test_reach_table_single_jump_limit_matches_physics(rise):
    single_abs, _, _ = REACH[rise][0]
    assert reach.can_cross(single_abs, rise, "single") if single_abs >= 0 else not reach.can_cross(0, rise, "single")
    assert not reach.can_cross(single_abs + 1, rise, "single")


@pytest.mark.parametrize("rise", sorted(REACH))
def test_reach_table_double_jump_is_doable_within_the_comfort_limit(rise):
    _, early_c, double_c = REACH[rise][1]
    assert reach.can_cross(early_c, rise, "early")
    assert reach.can_cross(double_c, rise, "double")
    assert reach.can_cross(REACH[rise][0][2], rise, "double")


@pytest.mark.parametrize("rise", sorted(DELAYED_GAPS))
def test_delayed_drops_need_the_late_double_jump(rise):
    for gap in DELAYED_GAPS[rise]:
        assert not reach.can_cross(gap, rise, "early")   # mit dem zweiten Sprung im höchsten Punkt reicht es nicht
        assert reach.can_cross(gap, rise, "double")      # verzögert im Fallen schon


def test_every_gap_in_generated_levels_is_doable_in_the_real_physics():
    pairs = {p for seed in range(3) for p in profile(generate_grid(seed, 2))}
    for gap, rise in sorted(pairs):
        assert reach.can_cross(gap, rise, "double"), (gap, rise)
        if gap > REACH[rise][0][0]:
            assert not reach.can_cross(gap, rise, "single"), (gap, rise)


def test_game_continues_with_generated_levels_and_keeps_score_and_lives():
    game = Game()
    assert game.level_number == 1 and game.level.cols == LEVEL_WIDTH
    game.score, game.lives = 450, 2
    game.state = "won"
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    game.handle_events()
    assert game.level_number == 2 and game.state == "playing"
    assert game.level.cols == 2 * LEVEL_WIDTH
    assert (game.score, game.lives) == (450, 2)
    game.next_level()
    assert game.level_number == 3 and game.level.cols == 2 * LEVEL_WIDTH


def test_restart_after_game_over_goes_back_to_level_one():
    game = Game()
    game.next_level()
    game.state = "game over"
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
    game.handle_events()
    assert game.level_number == 1 and game.score == 0 and game.lives == 3
