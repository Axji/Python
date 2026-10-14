"""Sortieralgorithmen (Bubble-, Shaker- und Quicksort) mit Zählern für Vergleiche und Vertauschungen."""
from global_lib import GlobalLib


class Sorting:
    """Sortierverfahren als statische Methoden.

    Die Klassenvariablen zählen, wie viele Vergleiche (`tests`) und Vertauschungen bzw.
    Verschiebungen (`moves`) der letzte Sortierlauf gebraucht hat.
    """

    tests = 0  # Anzahl Vergleiche
    moves = 0  # Anzahl Vertauschungen

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
    def bubble_sort(list_of_elements, verbose=False):
        """Bubblesort: vergleicht benachbarte Elemente und tauscht sie bei falscher Reihenfolge.

        Wiederholt die Durchläufe, bis nichts mehr getauscht wird. Laufzeit im schlechtesten Fall O(n²).
        Sortiert die übergebene Liste direkt und gibt sie zurück. Mit `verbose=True` wird jeder Tausch ausgegeben.
        """
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
                    GlobalLib.change_positions(list_of_elements, element, element+1, verbose)
        return list_of_elements

    @staticmethod
    def shaker_sort(list_of_elements, verbose=False):
        """Shakersort (Cocktailsort): Bubblesort, der abwechselnd vorwärts und rückwärts durch die Liste läuft.

        Kleine Elemente am Listenende wandern dadurch schneller nach vorne. Laufzeit im schlechtesten Fall O(n²).
        Sortiert die übergebene Liste direkt und gibt sie zurück. Mit `verbose=True` wird jeder Tausch ausgegeben.
        """
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
                        GlobalLib.change_positions(list_of_elements, element, element+1, verbose)
                if not swapped:
                    return list_of_elements

    @staticmethod
    def quick_sort(arr, verbose=False):
        """Quicksort: teilt die Liste um ein Pivot-Element in kleinere, gleiche und grössere Werte und sortiert die Teile rekursiv.

        Im Gegensatz zu den anderen Verfahren wird die Liste nicht verändert, sondern eine neue sortierte Liste
        zurückgegeben. Die Zähler werden nicht zurückgesetzt, dafür `reset_counters()` aufrufen.
        Laufzeit im Mittel O(n log n), im schlechtesten Fall O(n²).
        Quicksort tauscht hier nicht, sondern verteilt die Werte auf drei Listen. Mit `verbose=True` wird jede Verteilung
        ausgegeben (Wert, Pivot und Ziel-Liste).
        """
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
                if verbose:
                    print(f"Verschiebe {i} nach '{target}' (Pivot {pivot})")
            # Die beiden Teillisten rekursiv sortieren und zusammensetzen
            less = Sorting.quick_sort(less, verbose)
            more = Sorting.quick_sort(more, verbose)
            return less + pivot_list + more
