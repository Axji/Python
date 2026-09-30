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
    'sleepTimeBetweenFiles': '1',
    # Download-Adresse; XXX wird je Station durch deren Kürzel ersetzt
    'baseUrl': 'http://www.meteoschweiz.admin.ch/product/output/climate-data/'
               'homogenous-monthly-data-processing/data/homog_mo_XXX.txt',
    'stringToReplaceInUrl': 'XXX',
    'dataDir': 'daten',  # Ordner für die heruntergeladenen Dateien
    'Station': 'Station:',  # Textmarke der Zeile mit dem Stationsnamen
    # Kopfzeile direkt vor den Messwerten und ihre Länge (Anzahl Zeichen, um die Daten zu überspringen)
    'LineBeforeData': 'Year  Month        Temperature      Precipitation',
    'LineBeforeDataLen': '52',
}
config['global'] = {}
config['global']['Author'] = 'Axel "Axji" Zenklusen'

# Eine vorhandene config.ini nie überschreiben
with open(CONFIG_PATH, 'x', encoding='utf-8') as configfile:
    config.write(configfile)
