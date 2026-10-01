"""Liest die aktuelle Auslastung der Fitnesspark-Standorte aus und hängt sie an eine CSV-Datei an.

Pro Tag wird eine eigene Datei (Fitnespark_Belegung_JJJJ-MM-TT.csv) angelegt. Das Skript ist für den regelmässigen
Aufruf gedacht, etwa per Aufgabenplanung. Die CSV-Dateien können danach mit fitnessparks/fitnesspark_csv_to_sqlite.py
in die Datenbank geladen werden.
"""
import csv
import datetime as dt
import os
import time

import requests

REQUEST_TIMEOUT = 15  # Sekunden


class FitnessParkScraper:
    """
    Liest die Auslastungsdaten der Fitnessparks von einer Liste von URLs und speichert sie in einer CSV-Datei.

    Attribute:
        parks (list): Liste von Dictionaries, je eines pro Fitnesspark mit Name, ID und URL.
        output_filename (str): Name der CSV-Datei, in die die Daten geschrieben werden.
        header (list): Kopfzeile der CSV-Datei.
    """

    def __init__(self, parks, output_filename=None):
        """
        Erstellt den Scraper.

        Args:
            parks (list): Liste von Dictionaries, die die Fitnessparks beschreiben.
            output_filename (str, optional): Name der Ausgabedatei. Standard ist eine Datei mit dem heutigen Datum im Namen.
        """
        self.parks = parks
        if output_filename is None:
            self.output_filename = (
                "Fitnespark_Belegung_%s.csv" % dt.datetime.now().strftime("%Y-%m-%d")
            )
        else:
            self.output_filename = output_filename
        self.header = ["parkname", "anzahl", "current_datetime"]

    def create_header_if_not_exists(self):
        """
        Schreibt die Kopfzeile in die CSV-Datei, wenn die Datei neu oder leer ist.
        """
        file_exists = os.path.exists(self.output_filename)
        file_is_empty = not file_exists or os.path.getsize(self.output_filename) == 0
        if file_is_empty:
            with open(
                self.output_filename, "a", newline="", encoding="utf-8"
            ) as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(self.header)
            print(f"Header in '{self.output_filename}' created.")

    def fetch_and_store_url_data(self, park):
        """
        Ruft die Daten eines einzelnen Parks ab und hängt sie an die CSV-Datei an.

        Args:
            park (dict): Dictionary mit dem Namen und der URL des Parks.
        """
        current_datetime = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Daten von der URL abrufen
            response = requests.get(park["URL"], timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # Bei Fehlerstatus (z. B. 404 oder 500) eine Ausnahme auslösen

            data = response.json()

            if not data:
                print(
                    f"No data received from {park['URL']}. File '{self.output_filename}' was not updated."
                )
            else:
                # Daten an die CSV-Datei anhängen
                with open(
                    self.output_filename, "a", newline="", encoding="utf-8"
                ) as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([park["Name"], data, current_datetime])
                print(
                    f"Data from {park['URL']} successfully saved in '{self.output_filename}' at {current_datetime}"
                )

        except ValueError:
            # requests.exceptions.JSONDecodeError erbt von ValueError und RequestException,
            # daher muss dieser Zweig zuerst kommen.
            print(f"Error: Data from {park['URL']} is not valid JSON.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {park['URL']}: {e}")
        except IOError as e:
            print(f"Error writing to file '{self.output_filename}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def run(self):
        """
        Geht die Liste der Parks durch und ruft für jeden die Daten ab.
        """
        self.create_header_if_not_exists()
        for park in self.parks:
            self.fetch_and_store_url_data(park)


if __name__ == "__main__":
    # Liste der Fitnessparks, deren Auslastung abgerufen wird.
    # Jeder Park ist ein Dictionary mit Name, ID und der URL, die die aktuelle Besucherzahl liefert.
    fitnessparks = [
        {
            "Name": "Ostermundigen",
            "ID": 686,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=686&location_id=59&location_name=FP_Time-Out",
        },
        {
            "Name": "Bern-Stadt",
            "ID": 856,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=856&location_id=105&location_name=FP_Bern_City",
        },
        {
            "Name": "oberhofen-bern",
            "ID": 3014,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=3014&location_id=4&location_name=FP_Oberhofen Haupteingang",
        },
        {
            "Name": "oberhofen-hallenbad",
            "ID": 684,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=684&location_id=4&location_name=FP_Oberhofen Haupteingang",
        },
        {
            "Name": "baden-trafo",
            "ID": 680,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=680&location_id=57&location_name=FP_Trafo_Baden",
        },
        {
            "Name": "basel-heuwaage",
            "ID": 682,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=682&location_id=3&location_name=FP_Basel_Heuwaage",
        },
        {
            "Name": "luzern-allmend",
            "ID": 6778,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=6778&location_id=56&location_name=FP_Allmend_Luzern",
        },
        {
            "Name": "luzern-national",
            "ID": 690,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=690&location_id=54&location_name=FP_National_Luzern",
        },
        {
            "Name": "zug-eichstaette",
            "ID": 694,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=694&location_id=52&location_name=FP_Eichstaette_Zug",
        },
        {
            "Name": "greifensee-milandia",
            "ID": 2934,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=2934&location_id=12&location_name=FP_Milandia",
        },
        {
            "Name": "regensdorf",
            "ID": 700,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=700&location_id=1&location_name=FP_Regensdorf",
        },
        {
            "Name": "winterthur",
            "ID": 696,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=696&location_id=6&location_name=FP_Winterthur",
        },
        {
            "Name": "zuerich-glattpark",
            "ID": 698,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=698&location_id=31&location_name=FP_Glattpark",
        },
        {
            "Name": "puls-5-zuerich",
            "ID": 508,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=508&location_id=29&location_name=FP_Puls5",
        },
        {
            "Name": "zuerich-sihlcity",
            "ID": 704,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=704&location_id=34&location_name=FP_Sihlcity",
        },
        {
            "Name": "zuerich-stadelhofen",
            "ID": 702,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=702&location_id=30&location_name=FP_Stadelhofen",
        },
        {
            "Name": "zuerich-stockerhof",
            "ID": 706,
            "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=706&location_id=32&location_name=FP_Stockerhof",
        },
    ]

    # Scraper erstellen und ausführen
    scraper = FitnessParkScraper(fitnessparks)
    scraper.run()
