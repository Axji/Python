"""Tests für Conways Game of Life: Regeln, Linien zwischen Zellen und die Bedienung mit Maus und Tastatur (ohne Fenster)."""
import os
import random

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

import game_of_life as gol  # noqa: E402

BLINKER = {(5, 5), (6, 5), (7, 5)}
GLIDER = {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}


# ---------------------------------------------------------------- Regeln


def test_empty_field_stays_empty():
    assert gol.next_generation(set(), 10, 10) == set()


def test_single_cell_dies_of_loneliness():
    assert gol.next_generation({(3, 3)}, 10, 10) == set()


def test_block_is_stable():
    block = {(2, 2), (3, 2), (2, 3), (3, 3)}
    assert gol.next_generation(block, 10, 10) == block


def test_blinker_oscillates_with_period_two():
    vertical = {(6, 4), (6, 5), (6, 6)}
    assert gol.next_generation(BLINKER, 12, 12) == vertical
    assert gol.next_generation(vertical, 12, 12) == BLINKER


def test_dead_cell_with_exactly_three_neighbors_is_born():
    assert (1, 1) in gol.next_generation({(0, 0), (2, 0), (1, 2)}, 10, 10, wrap=False)


def test_overpopulation_kills_a_cell_with_four_neighbors():
    cross = {(5, 5), (4, 5), (6, 5), (5, 4), (5, 6)}  # Mitte hat vier Nachbarn
    assert (5, 5) not in gol.next_generation(cross, 12, 12)


def test_cell_with_two_or_three_neighbors_survives():
    assert (6, 5) in gol.next_generation(BLINKER, 12, 12)       # Mitte des Blinkers: zwei Nachbarn
    assert (5, 5) not in gol.next_generation(BLINKER, 12, 12)   # Ende: nur ein Nachbar


def test_glider_moves_one_cell_diagonally_every_four_generations():
    live = set(GLIDER)
    for _ in range(4):
        live = gol.next_generation(live, 20, 20)
    assert live == {(c + 1, r + 1) for c, r in GLIDER}


def test_wrap_around_keeps_a_glider_alive_forever():
    live = set(GLIDER)
    for _ in range(4 * 20):  # einmal rundherum
        live = gol.next_generation(live, 20, 20, wrap=True)
    assert live == GLIDER


def test_fixed_edge_lets_a_glider_end_as_a_block():
    live = set(GLIDER)
    for _ in range(200):
        live = gol.next_generation(live, 10, 10, wrap=False)
    assert live == {(8, 8), (9, 8), (8, 9), (9, 9)}  # klassisch: der Glider endet in der Ecke als stabiler Block


def test_wrap_connects_opposite_edges():
    # Drei Zellen in einer Reihe über die Nahtstelle (9, 0, 1): nur mit Torus sind sie Nachbarn und bilden einen Blinker
    live = {(9, 5), (0, 5), (1, 5)}
    assert gol.next_generation(live, 10, 10, wrap=True) == {(0, 4), (0, 5), (0, 6)}
    assert (0, 4) not in gol.next_generation(live, 10, 10, wrap=False)


# ---------------------------------------------------------------- Hilfsfunktionen


@pytest.mark.parametrize("start,end", [((0, 0), (5, 0)), ((0, 0), (0, 5)), ((0, 0), (5, 5)), ((5, 5), (0, 0)), ((2, 7), (9, 3))])
def test_line_has_both_ends_and_no_gaps(start, end):
    cells = gol.cells_on_line(start, end)
    assert cells[0] == start and cells[-1] == end
    for (c1, r1), (c2, r2) in zip(cells, cells[1:]):
        assert max(abs(c2 - c1), abs(r2 - r1)) == 1  # jede Zelle grenzt an die vorherige


def test_line_of_a_single_cell():
    assert gol.cells_on_line((4, 4), (4, 4)) == [(4, 4)]


def test_random_field_density_and_bounds():
    live = gol.random_field(40, 30, 0.3, random.Random(1))
    assert all(0 <= c < 40 and 0 <= r < 30 for c, r in live)
    assert 0.2 < len(live) / (40 * 30) < 0.4
    assert gol.random_field(10, 10, 0) == set()


# ---------------------------------------------------------------- Bedienung


@pytest.fixture
def app():
    return gol.LifeApp(cols=40, rows=30, cell=10)


def pos(app, col, row):
    """Bildschirmposition in der Mitte einer Zelle."""
    return col * app.cell + app.cell // 2, gol.TOOLBAR_H + row * app.cell + app.cell // 2


def mouse(app, kind, cell, button=1):
    p = pos(app, *cell)
    if kind == "down":
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=p, button=button)
    elif kind == "up":
        event = pygame.event.Event(pygame.MOUSEBUTTONUP, pos=p, button=button)
    else:
        event = pygame.event.Event(pygame.MOUSEMOTION, pos=p, rel=(0, 0), buttons=(button == 1, 0, button == 3))
    return app.handle_event(event)


def key(app, k):
    return app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k))


def test_left_click_sets_a_cell_and_right_click_removes_it(app):
    mouse(app, "down", (5, 5))
    mouse(app, "up", (5, 5))
    assert app.live == {(5, 5)}
    mouse(app, "down", (5, 5), button=3)
    mouse(app, "up", (5, 5), button=3)
    assert app.live == set()


def test_holding_the_left_button_draws_a_line_without_gaps(app):
    mouse(app, "down", (2, 2))
    mouse(app, "move", (30, 20))  # schneller Sprung: dazwischen dürfen keine Lücken bleiben
    mouse(app, "up", (30, 20))
    assert app.live == set(gol.cells_on_line((2, 2), (30, 20)))


def test_holding_the_right_button_erases_a_line(app):
    app.live = {(c, 10) for c in range(5, 25)}
    mouse(app, "down", (8, 10), button=3)
    mouse(app, "move", (18, 10), button=3)
    mouse(app, "up", (18, 10), button=3)
    assert app.live == {(c, 10) for c in range(5, 8)} | {(c, 10) for c in range(19, 25)}


def test_moving_without_a_pressed_button_changes_nothing(app):
    mouse(app, "move", (5, 5))
    mouse(app, "move", (9, 9))
    assert app.live == set()


def test_drawing_stops_after_the_button_is_released(app):
    mouse(app, "down", (3, 3))
    mouse(app, "up", (3, 3))
    mouse(app, "move", (20, 20))
    assert app.live == {(3, 3)}


def test_drawing_outside_the_field_is_ignored_without_error(app):
    mouse(app, "down", (0, 0))
    mouse(app, "move", (60, 40))  # weit rechts und unten ausserhalb des Felds
    assert all(app.in_field(cell) for cell in app.live)


def test_drawing_in_the_toolbar_sets_no_cells(app):
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(3, 3), button=3))
    assert app.live == set()


def test_can_draw_while_running(app):
    key(app, pygame.K_SPACE)
    mouse(app, "down", (4, 4))
    mouse(app, "up", (4, 4))
    assert app.running and (4, 4) in app.live


def test_space_starts_and_stops(app):
    assert not app.running
    key(app, pygame.K_SPACE)
    assert app.running
    key(app, pygame.K_SPACE)
    assert not app.running


def test_step_key_does_exactly_one_generation_and_works_while_stopped(app):
    app.live = set(BLINKER)
    key(app, pygame.K_s)
    assert app.generation == 1
    assert app.live == {(6, 4), (6, 5), (6, 6)}
    assert not app.running
    key(app, pygame.K_RIGHT)
    assert app.generation == 2 and app.live == BLINKER


def test_buttons_start_step_and_clear(app):
    app.live = set(BLINKER)
    by_text = {b.text(): b for b in app.buttons}
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=by_text["Schritt"].rect.center, button=1))
    assert app.generation == 1
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=by_text["Start"].rect.center, button=1))
    assert app.running
    assert {b.text() for b in app.buttons} >= {"Stop", "Schritt"}  # der Start-Knopf heisst jetzt Stop
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=by_text["Start"].rect.center, button=1))
    assert not app.running
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=by_text["Löschen"].rect.center, button=1))
    assert app.live == set() and app.generation == 0


def test_update_steps_only_while_running_and_in_time(app):
    app.live = set(BLINKER)
    app.update(10_000)
    assert app.generation == 0  # gestoppt: nichts passiert
    app.running = True
    app.last_step_ms = 0
    app.update(10_000)
    assert app.generation == 1
    app.update(10_000 + 1)  # zu früh für den nächsten Schritt
    assert app.generation == 1
    app.update(10_000 + 1000 // app.speed + 1)
    assert app.generation == 2


def test_clear_stops_the_simulation_and_resets_the_counter(app):
    app.live = set(BLINKER)
    app.running = True
    app.generation = 7
    key(app, pygame.K_c)
    assert app.live == set() and not app.running and app.generation == 0


def test_random_key_fills_the_field(app):
    key(app, pygame.K_z)
    assert len(app.live) > 0
    assert all(app.in_field(cell) for cell in app.live)


def test_speed_is_limited_to_the_available_steps(app):
    for _ in range(20):
        key(app, pygame.K_PLUS)
    assert app.speed == gol.SPEEDS[-1]
    for _ in range(20):
        key(app, pygame.K_MINUS)
    assert app.speed == gol.SPEEDS[0]


def test_t_toggles_the_edge_mode_and_it_changes_the_result(app):
    app.live = {(0, 5), (1, 5), (39, 5)}
    assert app.wrap
    key(app, pygame.K_t)
    assert not app.wrap
    fixed = gol.next_generation(app.live, app.cols, app.rows, app.wrap)
    key(app, pygame.K_t)
    assert app.wrap and gol.next_generation(app.live, app.cols, app.rows, app.wrap) != fixed


def test_escape_and_quit_end_the_program(app):
    assert key(app, pygame.K_ESCAPE) is False
    assert app.handle_event(pygame.event.Event(pygame.QUIT)) is False
    assert key(app, pygame.K_a) is True


def test_draw_runs_without_error(app):
    app.live = set(GLIDER)
    app.draw()
