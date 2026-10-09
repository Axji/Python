"""Demo-Skript: führt Bubblesort und Shakersort auf einer zufälligen, einer sortierten und einer umgekehrten Liste aus."""
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
print("Random")
List_to_sort = list(list_of_elements)  # Kopie, damit die Originalliste unverändert bleibt
print(Sorting.bubble_sort(List_to_sort))

print("Sorted")
List_to_sort = list(list_of_elements_sorted)
print(Sorting.bubble_sort(List_to_sort))

print("Reversed")
List_to_sort = list(list_of_elements_reversed)
print(Sorting.bubble_sort(List_to_sort))

# Shakersort
GlobalLib.print_title("Shakersort", 1)

print("Random")
List_to_sort = list(list_of_elements)
print(Sorting.shaker_sort(List_to_sort))

print("Sorted")
List_to_sort = list(list_of_elements_sorted)
print(Sorting.shaker_sort(List_to_sort))

print("Reversed")
List_to_sort = list(list_of_elements_reversed)
print(Sorting.shaker_sort(List_to_sort))
