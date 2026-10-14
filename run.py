"""Demo-Skript: führt Bubblesort, Shakersort und Quicksort (neue Liste und In-Place) auf einer zufälligen, einer sortierten und einer umgekehrten Liste aus.

Alle Aufrufe laufen mit `verbose=1`: am Ende jedes Laufs werden die Summen (Tausche bzw. Verschiebungen und Vergleiche) ausgegeben.
(`verbose=2` zeigt zusätzlich jeden einzelnen Tausch, `verbose=0` gibt nichts aus.)
"""
# from global_lib import *
from global_lib import GlobalLib
from sort import Sorting

# Testdaten: unsortiert, bereits sortiert und absteigend sortiert
list_of_elements = [2, 4, 8, 7, 5, 1, 8, 6, 4, 9, 5, 1, 5, 6]
list_of_elements_sorted = [1, 1, 2, 4, 4, 5, 5, 5, 6, 6, 7, 8, 8, 9]
list_of_elements_reversed = [9, 8, 8, 7, 6, 6, 5, 5, 5, 4, 4, 2, 1, 1]


# Hello World
GlobalLib.print_title("Hello world", 1)
print("Hello World")
GlobalLib.print_empty_lines(2)

# Bubblesort
GlobalLib.print_title("BubbleSort", 1)
print("Pseudo Random")
List_to_sort = list(list_of_elements)  # Kopie, damit die Originalliste unverändert bleibt
print(Sorting.bubble_sort(List_to_sort, verbose=1))

print("Sorted")
List_to_sort = list(list_of_elements_sorted)
print(Sorting.bubble_sort(List_to_sort, verbose=1))

print("Reversed")
List_to_sort = list(list_of_elements_reversed)
print(Sorting.bubble_sort(List_to_sort, verbose=1))

# Shakersort
GlobalLib.print_title("Shakersort", 1)

print("Random")
List_to_sort = list(list_of_elements)
print(Sorting.shaker_sort(List_to_sort, verbose=1))

print("Sorted")
List_to_sort = list(list_of_elements_sorted)
print(Sorting.shaker_sort(List_to_sort, verbose=1))

print("Reversed")
List_to_sort = list(list_of_elements_reversed)
print(Sorting.shaker_sort(List_to_sort, verbose=1))


# Quicksort (gibt eine neue sortierte Liste zurück, die Originalliste bleibt unverändert)
GlobalLib.print_title("Quicksort", 1)

print("Pseudo Random")
List_to_sort = list(list_of_elements)
print(Sorting.quick_sort(List_to_sort, verbose=1))

print("Sorted")
List_to_sort = list(list_of_elements_sorted)
print(Sorting.quick_sort(List_to_sort, verbose=1))

print("Reversed")
List_to_sort = list(list_of_elements_reversed)
print(Sorting.quick_sort(List_to_sort, verbose=1))


# Quicksort In-Place (tauscht in der übergebenen Liste wie Bubble- und Shakersort)
GlobalLib.print_title("Quicksort In-Place", 1)

print("Pseudo Random")
List_to_sort = list(list_of_elements)
print(Sorting.quick_sort_in_place(List_to_sort, verbose=1))

print("Sorted")
List_to_sort = list(list_of_elements_sorted)
print(Sorting.quick_sort_in_place(List_to_sort, verbose=1))

print("Reversed")
List_to_sort = list(list_of_elements_reversed)
print(Sorting.quick_sort_in_place(List_to_sort, verbose=1))
