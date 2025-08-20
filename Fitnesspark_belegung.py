import datetime as dt
import time
import requests
import csv
import os


def create_header_if_not_exists(filename: str, header: list):
    """
    Erstellt einen Header in der CSV-Datei, wenn diese neu und leer ist.
    """
    file_exists = os.path.exists(filename)
    file_is_empty = not file_exists or os.path.getsize(filename) == 0
    if file_is_empty:
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
        print(f"Header in '{filename}' erstellt.")


def fetch_and_store_url_data(url: str, output_file: str = "output_data_buffer.csv", parkname: str = "N/A"):
    """
    Ruft Daten von einer URL ab und speichert sie in einer CSV-Datei.
    Fügt einen Header hinzu, wenn die Datei neu erstellt wird.
    """
    # Header-Definition
    header = ["parkname", "anzahl", "current_datetime"]

    # Header erstellen, wenn die Datei neu und leer ist
    create_header_if_not_exists(output_file, header)

    current_datetime = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        if not data:
            print(f"Keine Daten von {url} erhalten. Datei '{output_file}' wurde nicht erstellt.")
        else:
            with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([parkname, data, current_datetime])
            print(f"Daten und Datum von {url} erfolgreich in '{output_file}' gespeichert. am {current_datetime}")

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der URL {url}: {e}")
    except ValueError:
        print(f"Fehler: Die Daten von {url} sind kein gültiges JSON.")
    except IOError as e:
        print(f"Fehler beim Schreiben der Datei '{output_file}': {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")


if __name__ == "__main__":
    fitnessparks = [
        {"Name": "Ostermundigen", "ID": 686,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=686&location_id=59&location_name=FP_Time-Out"},
        {"Name": "Bern-Stadt", "ID": 856,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=856&location_id=105&location_name=FP_Bern_City"},
        {"Name": "oberhofen-bern", "ID": 3014,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=3014&location_id=4&location_name=FP_Oberhofen Haupteingang"},
        {"Name": "oberhofen-hallenbad", "ID": 684,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=684&location_id=4&location_name=FP_Oberhofen Haupteingang"},
        {"Name": "baden-trafo", "ID": 680,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=680&location_id=57&location_name=FP_Trafo_Baden"},
        {"Name": "basel-heuwaage", "ID": 682,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=682&location_id=3&location_name=FP_Basel_Heuwaage"},
        {"Name": "luzern-allmend", "ID": 6778,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=6778&location_id=56&location_name=FP_Allmend_Luzern"},
        {"Name": "luzern-national", "ID": 690,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=690&location_id=54&location_name=FP_National_Luzern"},
        {"Name": "zug-eichstaette", "ID": 694,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=694&location_id=52&location_name=FP_Eichstaette_Zug"},
        {"Name": "greifensee-milandia", "ID": 2934,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=2934&location_id=12&location_name=FP_Milandia"},
        {"Name": "regensdorf", "ID": 700,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=700&location_id=1&location_name=FP_Regensdorf"},
        {"Name": "winterthur", "ID": 696,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=696&location_id=6&location_name=FP_Winterthur"},
        {"Name": "zuerich-glattpark", "ID": 698,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=698&location_id=31&location_name=FP_Glattpark"},
        {"Name": "puls-5-zuerich", "ID": 508,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=508&location_id=29&location_name=FP_Puls5"},
        {"Name": "zuerich-sihlcity", "ID": 784,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=704&location_id=34&location_name=FP_Sihlcity"},
        {"Name": "zuerich-stadelhofen", "ID": 702,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=702&location_id=30&location_name=FP_Stadelhofen"},
        {"Name": "zuerich-stockerhof", "ID": 706,
         "URL": "https://www.fitnesspark.ch/wp/wp-admin/admin-ajax.php?action=single_park_update_visitors&park_id=706&location_id=32&location_name=FP_Stockerhof"}
    ]

    outputFilename = "Fitnespark_Belegung_%s.csv" % dt.datetime.now().strftime("%Y-%m-%d")
    for fitnesspark in fitnessparks:
        url = str(fitnesspark['URL'])
        fetch_and_store_url_data(url, outputFilename, fitnesspark['Name'])
