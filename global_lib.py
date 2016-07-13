import os
import time
import datetime


class GlobalLib():

    @staticmethod
    def print_title(title, seconds=0):
        print("#################")
        print("## "+title)
        print("#################")
        time.sleep(seconds)

    @staticmethod
    def get_file_size(fullname):
        file_size = os.path.getsize(fullname)
        return file_size

    @staticmethod
    def get_file_path(fullname):
        file_path = os.path.abspath(fullname)
        return file_path

    @staticmethod
    def change_positions(list_of_elements, position_1, position_2):
        temp_element = list_of_elements[position_1]
        list_of_elements[position_1] = list_of_elements[position_2]
        list_of_elements[position_2] = temp_element

    @staticmethod
    def print_empty_lines(param):
        for i in range(0, param):
                print("")

    @staticmethod
    def date_iso():
        return datetime.date.today().isoformat()

    @staticmethod
    def date_time_iso():
        return datetime.datetime.now().isoformat()
