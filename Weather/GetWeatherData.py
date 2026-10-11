"""Lädt die homogenen Monatsdaten aller MeteoSchweiz-Stationen über die STAC-API und speichert sie.

Ablauf: Die Datensätze (Klimastationen und Niederschlagsstationen) werden über die API von data.geo.admin.ch abgefragt,
die Monatsdatei jeder Station wird heruntergeladen. Das Ergebnis landet an zwei Orten:
- eine CSV-Datei mit allen Stationen und dem Abrufzeitpunkt im Namen (Datenordner, z. B. homogene_monatsdaten_20261011_204500.csv)
- die SQLite-Datenbank weather.db im selben Ordner (Tabellen homogeneous_monthly, stations, parameters)
Die Einstellungen stehen in config.ini (erzeugt von Init/Config_Generator.py).
"""
import configparser
import csv
import datetime
import io
import json
import os
import sys
import time
import urllib.request

from SqlLiteWD import SqlLiteWD

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Konfiguration aus config.ini neben diesem Skript lesen
config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'config.ini'), encoding='utf-8')
cfg_data_dir = os.path.join(BASE_DIR, config['DEFAULT']['dataDir'])
cfg_api_url = config['DEFAULT']['apiUrl'].rstrip('/')
cfg_collections = [c.strip() for c in config['DEFAULT']['collections'].split(',') if c.strip()]
cfg_asset_suffix = config['DEFAULT']['assetSuffix']
cfg_sleep_time = float(config['DEFAULT']['sleepTimeBetweenFiles'])
REQUEST_TIMEOUT = 30  # Sekunden
PAGE_SIZE = 100  # Anzahl Stationen pro API-Abfrage


def http_get(url):
    """Lädt eine Adresse herunter und gibt den Inhalt als Text zurück."""
    req = urllib.request.Request(url)
    # Eigener User-Agent, damit der Server den Zugriff zuordnen kann
    req.add_header('User-Agent', 'weather-downloader/1.0 (Contact: axel.zenklusen@gmail.com)')
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        data = response.read()
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:  # Die Metadaten-Dateien sind teilweise in Windows-1252 kodiert
        return data.decode('cp1252')


def read_csv(text):
    """Liest eine Semikolon-getrennte CSV-Datei in eine Liste von Dictionaries."""
    return list(csv.DictReader(io.StringIO(text), delimiter=';'))


def list_monthly_files(collection):
    """Fragt die API ab und gibt für jede Station der Collection (Kürzel in Grossbuchstaben, Adresse der Monatsdatei) zurück."""
    files = []
    url = f"{cfg_api_url}/collections/{collection}/items?limit={PAGE_SIZE}"
    while url:
        page = json.loads(http_get(url))
        for item in page['features']:
            for name, asset in item['assets'].items():
                if name.endswith(cfg_asset_suffix):
                    files.append((item['id'].upper(), asset['href']))
        # Die API liefert die Stationen seitenweise; ohne "next"-Link ist die letzte Seite erreicht
        url = next((link['href'] for link in page.get('links', []) if link.get('rel') == 'next'), None)
    return files


def get_collection_metadata(collection):
    """Liest Stations- und Parameterbeschreibung einer Collection (als Listen von Dictionaries)."""
    assets = json.loads(http_get(f"{cfg_api_url}/collections/{collection}"))['assets']
    result = {}
    for kind in ('meta_stations.csv', 'meta_parameters.csv'):
        href = next(a['href'] for name, a in assets.items() if name.endswith(kind))
        result[kind] = read_csv(http_get(href))
    return result['meta_stations.csv'], result['meta_parameters.csv']


def to_float(text):
    """Wandelt eine Zahl aus der CSV in float um; leer = None (kein Messwert)."""
    text = text.strip()
    return float(text) if text else None


def month_start(timestamp):
    """Wandelt '01.03.1864 00:00' in '1864-03-01' um."""
    return datetime.datetime.strptime(timestamp, '%d.%m.%Y %H:%M').date().isoformat()


def write_combined_csv(rows, fieldnames, retrieved_at):
    """Schreibt alle Stationen in eine CSV-Datei mit dem Abrufzeitpunkt im Namen und gibt den Pfad zurück."""
    os.makedirs(cfg_data_dir, exist_ok=True)
    target = os.path.join(cfg_data_dir, 'homogene_monatsdaten_' + retrieved_at.strftime('%Y%m%d_%H%M%S') + '.csv')
    with open(target, 'w', encoding='utf-8', newline='') as f:
        # Die Datensätze haben unterschiedliche Spalten; fehlende Werte bleiben leer
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', restval='')
        writer.writeheader()
        writer.writerows(rows)
    return target


def load_all():
    """Lädt alle Stationen, schreibt CSV-Datei und Datenbank. Gibt die Anzahl fehlgeschlagener Stationen zurück."""
    retrieved_at = datetime.datetime.now().replace(microsecond=0)
    stamp = retrieved_at.isoformat()  # ISO 8601, z. B. 2026-10-11T22:44:02

    rows, fieldnames, values = [], ['station_abbr', 'reference_timestamp'], []
    stations, parameters, failed = {}, {}, []

    for collection in cfg_collections:
        print("Datensatz " + collection)
        meta_stations, meta_parameters = get_collection_metadata(collection)
        for s in meta_stations:
            stations[s['station_abbr']] = (
                s['station_abbr'], s['station_name'], s['station_canton'], to_float(s['station_height_masl']),
                to_float(s['station_coordinates_wgs84_lat']), to_float(s['station_coordinates_wgs84_lon']), collection)
        for p in meta_parameters:
            parameters[p['parameter_shortname']] = (
                p['parameter_shortname'], p['parameter_description_de'], p['parameter_description_en'],
                p['parameter_unit'])

        for station, href in list_monthly_files(collection):
            print(f"  {station}: {href}")
            try:
                station_rows = read_csv(http_get(href))
            except OSError as err:  # Netzwerk- und HTTP-Fehler; ein Fehler bei einer Station stoppt die anderen nicht
                print(f"  FEHLER bei {station}: {err}")
                failed.append(station)
                continue
            for row in station_rows:
                rows.append(row)
                # Datum immer als ISO speichern (die Quelle liefert TT.MM.JJJJ HH:MM)
                month = row['reference_timestamp'] = month_start(row['reference_timestamp'])
                for parameter, text in row.items():
                    if parameter in ('station_abbr', 'reference_timestamp'):
                        continue
                    if parameter not in fieldnames:
                        fieldnames.append(parameter)
                    value = to_float(text)
                    if value is not None:
                        values.append((row['station_abbr'], month, parameter, value))
            time.sleep(cfg_sleep_time)  # Pause zwischen den Downloads

    if not rows:
        print("Keine Daten geladen, nichts gespeichert.")
        return len(failed) or 1

    target = write_combined_csv(rows, fieldnames, retrieved_at)
    print(f"Datei gespeichert: {target} ({len(rows)} Zeilen)")

    with SqlLiteWD(os.path.join(cfg_data_dir, 'weather.db')) as db:
        db.save_stations(stations.values(), stamp)
        db.save_parameters(parameters.values(), stamp)
        count = db.save_monthly(values, stamp)
        print(f"Datenbank {db.db_path}: {count} Messwerte, {len(stations)} Stationen, {len(parameters)} Parameter")

    if failed:
        print("Nicht geladen: " + ", ".join(failed))
    return len(failed)


if __name__ == "__main__":
    sys.exit(1 if load_all() else 0)
