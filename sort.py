from global_lib import *

class Sorting():

    tests = 0
    moves = 0

    @staticmethod
    def reset_coutners():
        Sorting.tests = 0
        Sorting.moves = 0

    @staticmethod
    def print_counter():
        print("Tests done       = " + str(Sorting.tests))
        print("Permutation done = " + str(Sorting.moves))

    @staticmethod
    def bubble_sort(list_of_elements):
        Sorting.tests = 0
        Sorting.moves = 0
        swapped = True
        while swapped:
            swapped = False  # If we change nothing => is sorted
            for element in range(0, len(list_of_elements)-1):
                Sorting.tests += 1
                if list_of_elements[element] > list_of_elements[element + 1]:
                    Sorting.moves += 1
                    swapped = True  # We found two elements in the wrong order
                    GlobalLib.change_positions(list_of_elements, element, element+1)
        return list_of_elements

    @staticmethod
    def shaker_sort(list_of_elements):
        Sorting.tests = 0
        Sorting.moves = 0
        swapped = True
        up = range(len(list_of_elements)-1)
        while swapped:
            for indices in (up, reversed(up)):
                swapped = False  # If we change nothing => is sorted
                for element in indices:
                    Sorting.tests += 1
                    if list_of_elements[element] > list_of_elements[element + 1]:
                        Sorting.moves += 1
                        swapped = True  # We found two elements in the wrong order
                        GlobalLib.change_positions(list_of_elements, element, element+1)
                if not swapped:
                    return

    @staticmethod
    def quick_sort(arr):
        less = []
        pivot_list = []
        more = []
        if len(arr) <= 1:
            Sorting.tests += 1
            return arr
        else:
            pivot = arr[0]
            Sorting.moves += 1
            for i in arr:
                Sorting.tests += 1
                Sorting.moves += 1
                if i < pivot:
                    less.append(i)
                elif i > pivot:
                    more.append(i)
                else:
                    pivot_list.append(i)
            less = Sorting.quick_sort(less)
            more = Sorting.quick_sort(more)
            return less + pivot_list + more