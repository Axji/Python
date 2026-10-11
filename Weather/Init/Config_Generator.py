"""Erzeugt die Konfigurationsdatei Weather/config.ini mit den Standardwerten für GetWeatherData.py.

Einmalig ausführen. Eine bereits vorhandene config.ini wird nicht überschrieben (das Skript bricht dann mit einem Fehler ab).
"""
import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.ini')

config = configparser.ConfigParser()

# Schlüssel entsprechen denen, die Weather/GetWeatherData.py liest.
config['DEFAULT'] = {
    # Pause in Sekunden zwischen zwei Downloads, um den Server zu schonen
    'sleepTimeBetweenFiles': '0.5',
    # STAC-API von swisstopo/geo.admin.ch, über die MeteoSchweiz ihre Open-Government-Daten bereitstellt
    'apiUrl': 'https://data.geo.admin.ch/api/stac/v1',
    # Datensätze mit homogenen Messreihen: Klimastationen und Niederschlagsstationen
    'collections': 'ch.meteoschweiz.ogd-nbcn, ch.meteoschweiz.ogd-nbcn-precip',
    # Endung der Datei mit den Monatswerten (_d = Tag, _y = Jahr)
    'assetSuffix': '_m.csv',
    'dataDir': 'daten',  # Ordner für die heruntergeladenen Dateien und die Datenbank
}
config['global'] = {}
config['global']['Author'] = 'Axel "Axji" Zenklusen'

# Eine vorhandene config.ini nie überschreiben
with open(CONFIG_PATH, 'x', encoding='utf-8') as configfile:
    config.write(configfile)
