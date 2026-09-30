"""Kleine Hilfsfunktionen (Ausgabe, Dateien, Listen, Datum), die von mehreren Skripten genutzt werden."""
import os
import time
import datetime


class GlobalLib():
    """Sammlung statischer Hilfsfunktionen. Es wird keine Instanz benötigt."""

    @staticmethod
    def print_title(title, seconds=0):
        """Gibt den Titel als Kasten aus Rautenzeichen aus und wartet danach optional `seconds` Sekunden."""
        print("#################")
        print("## "+title)
        print("#################")
        time.sleep(seconds)

    @staticmethod
    def get_file_size(fullname):
        """Liefert die Dateigrösse in Bytes."""
        file_size = os.path.getsize(fullname)
        return file_size

    @staticmethod
    def get_file_path(fullname):
        """Liefert den absoluten Pfad zur angegebenen Datei."""
        file_path = os.path.abspath(fullname)
        return file_path

    @staticmethod
    def change_positions(list_of_elements, position_1, position_2):
        """Vertauscht zwei Elemente einer Liste direkt in der Liste (Dreieckstausch über ein Zwischenelement)."""
        temp_element = list_of_elements[position_1]
        list_of_elements[position_1] = list_of_elements[position_2]
        list_of_elements[position_2] = temp_element

    @staticmethod
    def print_empty_lines(param):
        """Gibt `param` Leerzeilen aus."""
        for i in range(0, param):
                print("")

    @staticmethod
    def date_iso():
        """Heutiges Datum als ISO-Text (JJJJ-MM-TT)."""
        return datetime.date.today().isoformat()

    @staticmethod
    def date_time_iso():
        """Aktuelles Datum mit Uhrzeit als ISO-Text."""
        return datetime.datetime.now().isoformat()


