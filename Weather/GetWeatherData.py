from urllib import request
import configparser
from global_lib import *
import os

config = configparser.ConfigParser()
config.read('config.ini')
cfg_data_dir = config['DEFAULT']['dataDir']


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
        print("Actual File =" + actual_url)
        response = opener.open(actual_url)
        # print(response.read())
        f = open(cfg_data_dir + '\\' + date_start + '_' + wetter_station + '.txt', 'w')
        response_str = response.read().decode("utf-8")
        # Jegliche art von Leerzeilen entfernen (Anscheinend gibt es ein Problem mit \r\r\n daher zuerst Fehlerkorrektur
        response_str = response_str.replace("\r\n", "\n")
        response_str = response_str.replace("\n\n", "\n")
        response_str = response_str.replace("\n\n", "\n")
        # filtered = os.linesep.join([s for s in responseStr.splitlines(True) if s.strip("\r\n")])
        f.write(response_str)
        time.sleep(cfg_sleep_time_between_files)


def get_date_from_file(file):
    datestring = file[:10]
    return datetime.datetime.strptime(datestring, '%Y-%m-%d').date()


def parse_content(data):
    pass


def parse_files():
    max_date = datetime.datetime.strptime('1980-05-14', '%Y-%m-%d').date()
    file_list = os.listdir(cfg_data_dir)
    for file in file_list:
        filedate = get_date_from_file(file)
        if filedate > max_date:
            max_date = filedate

    for file in file_list:
        if file.startswith(max_date.isoformat()):
            with open(cfg_data_dir + '\\' +file, 'r') as actfile:
                data = actfile.read()
                parse_content(data)

    # place code here
    return 1


#get_files_from_web()
parse_files()

# print(page)
