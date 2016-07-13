from urllib import request
import configparser
from global_lib import *
import re

config = configparser.ConfigParser()
config.read('config.ini')


def get_files_from_web():
    opener = request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    wetter_stations = ['SIO', 'BER', 'BAS', 'CHM', 'CHD', 'GSB',
                       'DAV', 'ENG', 'GVE', 'LUG', 'PAY', 'SIA',
                       'SAE', 'SMA']
    cfg_base_url = config['DEFAULT']['baseUrl']
    cfg_string_to_replace_in_url = config['DEFAULT']['stringToReplaceInUrl']
    cfg_sleep_time_between_files = int(config['DEFAULT']['sleepTimeBetweenFiles'])

    date_start = GlobalLib.date_iso()
    # datetime.datetime.now().isoformat().replace('.', '_').replace(':', '')
    for wetter_station in wetter_stations:
        actual_url = cfg_base_url.replace(cfg_string_to_replace_in_url, wetter_station)
        print("Actual File ="+ actual_url)
        response = opener.open(actual_url)
        # print(response.read())
        f = open('daten\\' + date_start + '_' + wetter_station + '.txt', 'w')
        response_str = response.read().decode("utf-8")
        # Jegliche art von Leerzeilen entfernen (Anscheinend gibt es ein Problem mit \r\r\n daher zuerst Fehlerkorrektur
        response_str = response_str.replace("\r\n", "\n")
        response_str = response_str.replace("\n\n", "\n")
        response_str = response_str.replace("\n\n", "\n")
        #   filtered = os.linesep.join([s for s in responseStr.splitlines(True) if s.strip("\r\n")])
        f.write(response_str)
        time.sleep(cfg_sleep_time_between_files)

def parse_files():


get_files_from_web()
parse_files()





#page = request.urlopen("http://www.meteoschweiz.admin.ch/product/output/climate-data/homogenous-monthly-data-processing/data/homog_mo_SIO.txt").read()
#page = request.urlopen("http://www.meteoschweiz.admin.ch/product/output/climate-data/homogenous-monthly-data-processing/data/homog_mo_BER.txt").read()
#page = request.urlopen("http://www.google.com").read()



#from os import walk
#dir = 'C:\\Users\\azen\\Documents\\WetterDaten'


#f = []
#for (dirpath, dirnames, filenames) in walk(dir):
#    f.extend(filenames)
#    break


#print(page)


