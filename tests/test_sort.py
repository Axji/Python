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
@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort, Sorting.quick_sort, Sorting.quick_sort_in_place])
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
    algorithm(data, verbose=2)
    lines = capsys.readouterr().out.strip().splitlines()
    swaps, summary = lines[:-1], lines[-1]
    assert len(swaps) == Sorting.moves == 2  # genau ein Ausdruck je Tausch
    assert all(line.startswith("Tausche Position") for line in swaps)
    assert swaps[-1].endswith("[1, 2, 3]")
    assert summary.startswith("Fertig: 2 Tausche, ")  # am Ende die Zahl der Tausche


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort, Sorting.quick_sort, Sorting.quick_sort_in_place])
def test_not_verbose_prints_nothing(algorithm, capsys):
    algorithm([3, 1, 2])
    assert capsys.readouterr().out == ""


def test_verbose_quick_sort_prints_each_distribution(capsys):
    assert Sorting.quick_sort([3, 1, 2], verbose=2) == [1, 2, 3]
    out = capsys.readouterr().out
    assert "Verschiebe 1 nach 'kleiner' (Pivot 3)" in out
    assert "Verschiebe 3 nach 'gleich' (Pivot 3)" in out


def test_verbose_gives_same_result_as_silent(capsys):
    assert Sorting.bubble_sort([5, 2, 9, 1], verbose=2) == Sorting.bubble_sort([5, 2, 9, 1])


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort])
def test_verbose_summary_counts_swaps_and_tests(algorithm, capsys):
    algorithm([5, 4, 3, 2, 1], verbose=2)
    summary = capsys.readouterr().out.strip().splitlines()[-1]
    assert summary == f"Fertig: {Sorting.moves} Tausche, {Sorting.tests} Vergleiche"
    assert Sorting.moves == 10  # umgekehrte Liste mit 5 Elementen braucht 10 Tausche


def test_verbose_summary_singular_and_zero(capsys):
    Sorting.bubble_sort([2, 1], verbose=2)
    assert "Fertig: 1 Tausch, " in capsys.readouterr().out
    Sorting.shaker_sort([1, 2, 3], verbose=2)
    assert "Fertig: 0 Tausche, " in capsys.readouterr().out


def test_verbose_quick_sort_summary_matches_printed_lines(capsys):
    Sorting.reset_counters()
    Sorting.quick_sort([3, 1, 2, 3], verbose=2)
    lines = capsys.readouterr().out.strip().splitlines()
    distributions = [line for line in lines if line.startswith("Verschiebe ")]
    assert lines[-1].startswith(f"Fertig: {len(distributions)} Verschiebungen, ")  # Zahl stimmt mit den Zeilen überein


def test_verbose_quick_sort_summary_counts_only_this_call(capsys):
    Sorting.quick_sort([3, 1, 2], verbose=2)
    first = capsys.readouterr().out.strip().splitlines()[-1]
    Sorting.quick_sort([3, 1, 2], verbose=2)  # Zähler wurden nicht zurückgesetzt, trotzdem gleiche Zusammenfassung
    second = capsys.readouterr().out.strip().splitlines()[-1]
    assert first == second


# ---------------------------------------------------------------- Ausgabe-Stufen (verbose 0, 1, 2)


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort, Sorting.quick_sort, Sorting.quick_sort_in_place])
def test_level_0_prints_nothing(algorithm, capsys):
    algorithm([3, 1, 2], verbose=0)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort])
def test_level_1_prints_only_the_summary(algorithm, capsys):
    algorithm([3, 1, 2], verbose=1)
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0].startswith("Fertig: 2 Tausche, ")
    assert len(lines) == 1  # kein einzelner Tausch


def test_level_1_quick_sort_prints_only_the_summary(capsys):
    Sorting.quick_sort([3, 1, 2], verbose=1)
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("Fertig: ")


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort, Sorting.quick_sort, Sorting.quick_sort_in_place])
def test_level_2_prints_details_and_summary(algorithm, capsys):
    algorithm([3, 1, 2], verbose=2)
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) > 1
    assert lines[-1].startswith("Fertig: ")


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort, Sorting.quick_sort, Sorting.quick_sort_in_place])
def test_level_2_output_contains_level_1_output(algorithm, capsys):
    algorithm([5, 2, 4, 1], verbose=1)
    summary = capsys.readouterr().out.strip()
    algorithm([5, 2, 4, 1], verbose=2)
    detailed = capsys.readouterr().out.strip().splitlines()
    assert detailed[-1] == summary  # Stufe 2 endet mit der Zusammenfassung von Stufe 1


def test_true_counts_as_level_1_and_false_as_level_0(capsys):
    Sorting.bubble_sort([2, 1], verbose=True)
    assert capsys.readouterr().out.strip().splitlines() == ["Fertig: 1 Tausch, 2 Vergleiche"]
    Sorting.bubble_sort([2, 1], verbose=False)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("algorithm", [Sorting.bubble_sort, Sorting.shaker_sort, Sorting.quick_sort, Sorting.quick_sort_in_place])
@pytest.mark.parametrize("level", [3, -1, "2", None])
def test_invalid_level_raises(algorithm, level):
    with pytest.raises(ValueError):
        algorithm([2, 1], verbose=level)


# ---------------------------------------------------------------- Quicksort In-Place


def test_in_place_quick_sort_sorts_the_given_list_and_returns_it():
    data = [3, 1, 2, 3, 0]
    result = Sorting.quick_sort_in_place(data)
    assert result is data  # dieselbe Liste, nicht eine neue
    assert data == [0, 1, 2, 3, 3]


def test_in_place_quick_sort_matches_sorted_on_many_random_lists():
    rng = random.Random(42)
    for _ in range(300):
        data = [rng.randrange(20) for _ in range(rng.randrange(0, 30))]
        assert Sorting.quick_sort_in_place(list(data)) == sorted(data)


def test_in_place_quick_sort_handles_sorted_and_equal_lists_without_deep_recursion():
    big_sorted = list(range(2000))
    assert Sorting.quick_sort_in_place(list(big_sorted)) == big_sorted
    assert Sorting.quick_sort_in_place([7] * 300) == [7] * 300


def test_in_place_quick_sort_verbose_prints_every_swap_and_summary(capsys):
    data = [5, 2, 4, 1, 3]
    Sorting.quick_sort_in_place(data, verbose=2)
    lines = capsys.readouterr().out.strip().splitlines()
    swaps, summary = lines[:-1], lines[-1]
    assert len(swaps) == Sorting.moves
    assert all(line.startswith("Tausche Position") for line in swaps)
    assert swaps[-1].endswith("[1, 2, 3, 4, 5]")
    assert summary == f"Fertig: {Sorting.moves} Tausche, {Sorting.tests} Vergleiche"


def test_in_place_quick_sort_level_1_prints_only_summary(capsys):
    Sorting.quick_sort_in_place([5, 2, 4, 1, 3], verbose=1)
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("Fertig: ")


def test_in_place_quick_sort_resets_counters_each_call():
    Sorting.quick_sort_in_place([5, 2, 4, 1, 3])
    first = (Sorting.tests, Sorting.moves)
    Sorting.quick_sort_in_place([5, 2, 4, 1, 3])
    assert (Sorting.tests, Sorting.moves) == first  # wie Bubble- und Shakersort: Zähler beginnen neu


def test_in_place_quick_sort_needs_no_swaps_on_one_element_or_empty_list():
    assert Sorting.quick_sort_in_place([]) == []
    assert Sorting.quick_sort_in_place([4]) == [4]
    assert Sorting.moves == 0
