import random

import pytest

from sort import Sorting

CASES = {
    "leer": [],
    "ein Element": [1],
    "sortiert": [1, 2, 3, 4, 5],
    "umgekehrt": [5, 4, 3, 2, 1],
    "doppelte Werte": [3, 1, 3, 2, 1],
    "zufällig": random.Random(1).sample(range(100), 30),
}


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort, Sorting.quick_sort])
def test_sorts_like_sorted(algorithm, name):
    data = list(CASES[name])
    assert algorithm(data) == sorted(CASES[name])


def test_bubble_sort_sorts_in_place():
    data = [3, 1, 2]
    result = Sorting.bubble_sort(data)
    assert result is data
    assert data == [1, 2, 3]


def test_quick_sort_keeps_input_unchanged():
    data = [3, 1, 2]
    Sorting.quick_sort(data)
    assert data == [3, 1, 2]


def test_counters_are_reset_and_counted():
    Sorting.bubble_sort([2, 1])
    assert (Sorting.tests, Sorting.moves) == (2, 1)
    Sorting.reset_counters()
    assert (Sorting.tests, Sorting.moves) == (0, 0)


def test_sorted_list_needs_no_moves():
    Sorting.bubble_sort([1, 2, 3])
    assert Sorting.moves == 0


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort])
def test_verbose_prints_every_swap(algorithm, capsys):
    data = [3, 1, 2]
    algorithm(data, verbose=True)
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == Sorting.moves == 2  # genau ein Ausdruck je Tausch
    assert all(line.startswith("Tausche Position") for line in lines)
    assert lines[-1].endswith("[1, 2, 3]")


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort, Sorting.quick_sort])
def test_not_verbose_prints_nothing(algorithm, capsys):
    algorithm([3, 1, 2])
    assert capsys.readouterr().out == ""


def test_verbose_quick_sort_prints_each_distribution(capsys):
    assert Sorting.quick_sort([3, 1, 2], verbose=True) == [1, 2, 3]
    out = capsys.readouterr().out
    assert "Verschiebe 1 nach 'kleiner' (Pivot 3)" in out
    assert "Verschiebe 3 nach 'gleich' (Pivot 3)" in out


def test_verbose_gives_same_result_as_silent(capsys):
    assert Sorting.bubble_sort([5, 2, 9, 1], verbose=True) == Sorting.bubble_sort([5, 2, 9, 1])
