"""Sortieralgorithmen (Bubble-, Shaker- und Quicksort, Quicksort auch als In-Place-Version) mit Zählern für Vergleiche
und Vertauschungen."""
from global_lib import GlobalLib


class Sorting:
    """Sortierverfahren als statische Methoden.

    Die Klassenvariablen zählen, wie viele Vergleiche (`tests`) und Vertauschungen bzw.
    Verschiebungen (`moves`) der letzte Sortierlauf gebraucht hat.
    """

    tests = 0  # Anzahl Vergleiche
    moves = 0  # Anzahl Vertauschungen
    # Ausgabe-Stufen für den Parameter `verbose` der Sortierverfahren:
    #   0 = keine Ausgabe, 1 = nur Summen (Tausche und Vergleiche), 2 = Summen und jeder einzelne Tausch
    distributions = 0  # Quicksort: Anzahl Verteilungen auf kleiner/gleich/grösser im letzten Aufruf (ohne Pivot-Wahl)

    @staticmethod
    def reset_counters():
        """Setzt beide Zähler auf 0 zurück."""
        Sorting.tests = 0
        Sorting.moves = 0

    @staticmethod
    def print_counter():
        """Gibt die Zähler des letzten Sortierlaufs aus."""
        print("Tests done       = " + str(Sorting.tests))
        print("Permutation done = " + str(Sorting.moves))

    @staticmethod
    def bubble_sort(list_of_elements, verbose=0):
        """Bubblesort: vergleicht benachbarte Elemente und tauscht sie bei falscher Reihenfolge.

        Wiederholt die Durchläufe, bis nichts mehr getauscht wird. Laufzeit im schlechtesten Fall O(n²).
        Sortiert die übergebene Liste direkt und gibt sie zurück. Ausgabe über `verbose`: 0 keine, 1 Summen, 2 auch jeder Tausch.
        """
        Sorting._check_verbose(verbose)
        Sorting.tests = 0
        Sorting.moves = 0
        swapped = True
        while swapped:
            swapped = False  # Wird in einem Durchlauf nichts getauscht, ist die Liste sortiert
            for element in range(0, len(list_of_elements)-1):
                Sorting.tests += 1
                if list_of_elements[element] > list_of_elements[element + 1]:
                    Sorting.moves += 1
                    swapped = True  # Zwei Elemente in falscher Reihenfolge gefunden
                    GlobalLib.change_positions(list_of_elements, element, element+1, verbose >= 2)
        if verbose >= 1:
            Sorting._print_summary("Tausch", "Tausche", Sorting.moves, Sorting.tests)
        return list_of_elements

    @staticmethod
    def shaker_sort(list_of_elements, verbose=0):
        """Shakersort (Cocktailsort): Bubblesort, der abwechselnd vorwärts und rückwärts durch die Liste läuft.

        Kleine Elemente am Listenende wandern dadurch schneller nach vorne. Laufzeit im schlechtesten Fall O(n²).
        Sortiert die übergebene Liste direkt und gibt sie zurück. Ausgabe über `verbose`: 0 keine, 1 Summen, 2 auch jeder Tausch.
        """
        Sorting._check_verbose(verbose)
        Sorting.tests = 0
        Sorting.moves = 0
        swapped = True
        up = range(len(list_of_elements)-1)  # Indizes für die Vorwärtsrichtung; reversed(up) für die Rückrichtung
        while swapped:
            for indices in (up, reversed(up)):
                swapped = False  # Wird in einer Richtung nichts getauscht, ist die Liste sortiert
                for element in indices:
                    Sorting.tests += 1
                    if list_of_elements[element] > list_of_elements[element + 1]:
                        Sorting.moves += 1
                        swapped = True  # Zwei Elemente in falscher Reihenfolge gefunden
                        GlobalLib.change_positions(list_of_elements, element, element+1, verbose >= 2)
                if not swapped:
                    if verbose >= 1:
                        Sorting._print_summary("Tausch", "Tausche", Sorting.moves, Sorting.tests)
                    return list_of_elements

    @staticmethod
    def quick_sort(arr, verbose=0):
        """Quicksort: teilt die Liste um ein Pivot-Element in kleinere, gleiche und grössere Werte und sortiert die Teile rekursiv.

        Im Gegensatz zu den anderen Verfahren wird die Liste nicht verändert, sondern eine neue sortierte Liste
        zurückgegeben. Die Zähler werden nicht zurückgesetzt, dafür `reset_counters()` aufrufen.
        Laufzeit im Mittel O(n log n), im schlechtesten Fall O(n²).
        Quicksort tauscht hier nicht, sondern verteilt die Werte auf drei Listen. Ausgabe über `verbose`: 0 keine,
        1 Summen (Verschiebungen und Vergleiche dieses Aufrufs), 2 auch jede einzelne Verteilung (Wert, Pivot, Ziel-Liste).
        """
        Sorting._check_verbose(verbose)
        tests_before = Sorting.tests  # die Zähler laufen weiter, gezählt wird die Differenz
        Sorting.distributions = 0
        result = Sorting._quick_sort(arr, verbose)
        if verbose >= 1:
            Sorting._print_summary("Verschiebung", "Verschiebungen", Sorting.distributions, Sorting.tests - tests_before)
        return result

    @staticmethod
    def quick_sort_in_place(list_of_elements, verbose=0):
        """Quicksort, der wie Bubble- und Shakersort in der übergebenen Liste tauscht (In-Place) und sie zurückgibt.

        Als Pivot dient das mittlere Element des jeweiligen Bereichs. Es wird ans Ende getauscht, danach wandern alle
        kleineren Werte nach vorne und das Pivot an seinen endgültigen Platz. Die beiden Teilbereiche werden rekursiv
        sortiert, der kleinere zuerst, damit die Rekursion flach bleibt. Laufzeit im Mittel O(n log n), im schlechtesten
        Fall O(n²). Ausgabe über `verbose`: 0 keine, 1 Summen, 2 auch jeder Tausch.
        """
        Sorting._check_verbose(verbose)
        Sorting.tests = 0
        Sorting.moves = 0
        Sorting._quick_sort_in_place(list_of_elements, 0, len(list_of_elements) - 1, verbose)
        if verbose >= 1:
            Sorting._print_summary("Tausch", "Tausche", Sorting.moves, Sorting.tests)
        return list_of_elements

    @staticmethod
    def _quick_sort_in_place(list_of_elements, low, high, verbose):
        """Sortiert den Bereich von `low` bis `high` (beide eingeschlossen) in der Liste."""
        while low < high:
            pivot_position = Sorting._partition(list_of_elements, low, high, verbose)
            # Den kleineren Teil rekursiv, den grösseren in der Schleife sortieren: die Rekursionstiefe bleibt klein
            if pivot_position - low < high - pivot_position:
                Sorting._quick_sort_in_place(list_of_elements, low, pivot_position - 1, verbose)
                low = pivot_position + 1
            else:
                Sorting._quick_sort_in_place(list_of_elements, pivot_position + 1, high, verbose)
                high = pivot_position - 1

    @staticmethod
    def _partition(list_of_elements, low, high, verbose):
        """Teilt den Bereich um das Pivot und gibt dessen endgültige Position zurück. Links davon stehen nur kleinere Werte."""
        middle = (low + high) // 2
        if middle != high:
            Sorting._swap(list_of_elements, middle, high, verbose)  # Pivot ans Ende, damit es beim Teilen nicht im Weg ist
        pivot = list_of_elements[high]
        store = low  # Position, an die der nächste kleinere Wert gehört
        for position in range(low, high):
            Sorting.tests += 1
            if list_of_elements[position] < pivot:
                if position != store:
                    Sorting._swap(list_of_elements, position, store, verbose)
                store += 1
        if store != high:
            Sorting._swap(list_of_elements, store, high, verbose)  # Pivot an seinen endgültigen Platz
        return store

    @staticmethod
    def _swap(list_of_elements, position_1, position_2, verbose):
        """Tauscht zwei Elemente, zählt den Tausch und gibt ihn ab Stufe 2 aus."""
        Sorting.moves += 1
        GlobalLib.change_positions(list_of_elements, position_1, position_2, verbose >= 2)

    @staticmethod
    def _check_verbose(verbose):
        """Erlaubt sind 0, 1 und 2 (True zählt als 1, False als 0). Alles andere ist ein Fehler."""
        if verbose not in (0, 1, 2):
            raise ValueError(f"verbose muss 0, 1 oder 2 sein, nicht {verbose!r}")

    @staticmethod
    def _print_summary(singular, plural, count, tests):
        """Zusammenfassung am Ende eines Laufs ab verbose=1: wie viele Tausche/Verschiebungen und Vergleiche es gab."""
        print(f"Fertig: {count} {singular if count == 1 else plural}, {tests} Vergleiche")

    @staticmethod
    def _quick_sort(arr, verbose):
        """Rekursiver Teil von `quick_sort`. Die Zusammenfassung kommt nur einmal, vom äusseren Aufruf."""
        less = []        # Werte kleiner als das Pivot-Element
        pivot_list = []  # Werte, die dem Pivot-Element entsprechen
        more = []        # Werte grösser als das Pivot-Element
        if len(arr) <= 1:  # Abbruchbedingung der Rekursion: eine leere oder einelementige Liste ist sortiert
            Sorting.tests += 1
            return arr
        else:
            pivot = arr[0]  # Einfachste Pivot-Wahl: das erste Element
            Sorting.moves += 1
            for i in arr:
                Sorting.tests += 1
                Sorting.moves += 1
                if i < pivot:
                    less.append(i)
                    target = "kleiner"
                elif i > pivot:
                    more.append(i)
                    target = "grösser"
                else:
                    pivot_list.append(i)
                    target = "gleich"
                Sorting.distributions += 1
                if verbose >= 2:
                    print(f"Verschiebe {i} nach '{target}' (Pivot {pivot})")
            # Die beiden Teillisten rekursiv sortieren und zusammensetzen
            less = Sorting._quick_sort(less, verbose)
            more = Sorting._quick_sort(more, verbose)
            return less + pivot_list + more
