import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.ini')

config = configparser.ConfigParser()

# Schlüssel entsprechen denen, die Weather/GetWeatherData.py liest.
config['DEFAULT'] = {
    'sleepTimeBetweenFiles': '1',
    'baseUrl': 'http://www.meteoschweiz.admin.ch/product/output/climate-data/'
               'homogenous-monthly-data-processing/data/homog_mo_XXX.txt',
    'stringToReplaceInUrl': 'XXX',
    'dataDir': 'daten',
    'Station': 'Station:',
    'LineBeforeData': 'Year  Month        Temperature      Precipitation',
    'LineBeforeDataLen': '52',
}
config['global'] = {}
config['global']['Author'] = 'Axel "Axji" Zenklusen'

# Eine vorhandene config.ini nie überschreiben
with open(CONFIG_PATH, 'x', encoding='utf-8') as configfile:
    config.write(configfile)
