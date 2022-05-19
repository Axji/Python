import urllib.request
import configparser
import time
import datetime
import os

import pyodbc as pyodbc

config = configparser.ConfigParser()
config.read('config.ini')
cfg_data_dir = config['DEFAULT']['dataDir']
debugLevel = 3


def debug_print(debug_text, debug_lvl):
    """Druckt Meldungen mit Führendem Marker in die Console"""
    if debugLevel < debug_lvl:
        return
    print("### - " + debug_text[:500])


def get_files_from_web():
    """Für jede in wetter_stations, Gepflegte Station werden die Aktuellen Wetterdatenabgerufen"""
    debug_print("get_files_from_web()",1)

    wetter_stations = ['SIO', 'BER', 'BAS', 'CHM', 'CHD', 'GSB',
                       'DAV', 'ENG', 'GVE', 'LUG', 'PAY', 'SIA',
                       'SAE', 'SMA']
    cfg_base_url = config['DEFAULT']['baseUrl']
    cfg_string_to_replace_in_url = config['DEFAULT']['stringToReplaceInUrl']
    cfg_sleep_time_between_files = int(config['DEFAULT']['sleepTimeBetweenFiles'])

    date_start = datetime.date.today().isoformat()
    for wetter_station in wetter_stations:
        actual_url = cfg_base_url.replace(cfg_string_to_replace_in_url, wetter_station)
        print("Actual File =" + actual_url)

        req = urllib.request.Request(actual_url)
        req.add_header('User-Agent', 'urllib-example/0.1 (Contact: . . .)')

        response = urllib.request.urlopen(req)

        html_content = response.read()

        html_content = str(html_content)
        html_content = html_content.replace("\\r\\n", "\n")
        html_content = html_content.replace("\n\n", "\n")
        html_content = html_content.replace("\n\n", "\n")

        # print(response.read())
        f = open(cfg_data_dir + '\\' + date_start + '_' + wetter_station + '.txt', 'w')

        f.write(html_content)
        time.sleep(cfg_sleep_time_between_files)


def get_date_from_file(file):
    """Holt das Dautm aus dem Header der Datei"""
    debug_print("get_date_from_file("+file+")", 1)

    datestring = file[:10]
    extracteddate = datetime.datetime.strptime(datestring, '%Y-%m-%d').date()
    debug_print("Extracted Date " + extracteddate.strftime('%Y-%m-%d'), 3)
    return extracteddate


def parse_content(filecontent):
    """Loopt über den Header und die Zeilen des files und liest die passenden Daten aus schreibt diese danach in die lokale Datenbank"""
    # Markante Stellen im Textfile markieren
    station_pos = str.find(filecontent, config['DEFAULT']['Station'])
    debug_print("station_pos = " + str(station_pos), 5)
    station_line_end = str.find(filecontent, "\n", station_pos)
    debug_print("station_line_end = " + str(station_line_end), 5)
    data_pos = str.find(filecontent, config['DEFAULT']['LineBeforeData'])
    debug_print("data_pos = " + str(data_pos), 5)
    data_pos += int(config['DEFAULT']['LineBeforeDataLen'])
    debug_print("data_pos + LineBeforeData = " + str(data_pos), 5)
    station_line = filecontent[station_pos:station_line_end]

    debug_print(station_line, 5)
    station = station_line[str.find(station_line, "    "):].strip()
    debug_print(station, 4)

    debug_print(filecontent[data_pos:], 4)

    conn_str = ("Driver={SQL Server Native Client 11.0};"
                "Server=localhost\\SQLEXPRESS;"
                "Database=weather;"
                "UID=weather;"
                "PWD=weather;")

    conn = pyodbc.connect(conn_str)
    conn.autocommit = True

    cursor = conn.cursor()

    baseSQL = """INSERT INTO [Landing_Weather] 
        ([Station] ,[Jahr] ,[Monat] ,[Temp] ,[Rain] ,[loaddate]) 
        VALUES (?,?,?,?,?,?);"""

    #baseSQL = """  INSERT INTO [dbo].[Landing_Weather] ([Station] ,[Jahr] ,[Monat] ,[Temp] ,[Rain] ,[loaddate]) VALUES ('A',1980,5,14,0,'2021-04-27')"""

    for line in filecontent[data_pos:].split("\n"):
        if len(line) > 20:
            year = int(line[0:4])
            month = int(line[9:11])
            temp = -999.9
            rain = -999.9
            if line[25:30] != '   NA':
                temp = float(line[25:30])
            if line[44:49] != '   NA':
                rain = float(line[44:49])

            cursor.execute(baseSQL, (station, year, month, temp, rain, datetime.datetime.now()))

    return 0


def parse_files():
    """Liest alle Files aus dem Datenverzeichnis und wählt die Files mit dem höchstem Datum aus"""
    max_date = datetime.datetime.strptime('1980-05-14', '%Y-%m-%d').date()
    file_list = os.listdir(cfg_data_dir)
    for file in file_list:
        file_date = get_date_from_file(file)
        if file_date > max_date:
            max_date = file_date

    for file in file_list:
        if file.startswith(max_date.isoformat()):
            with open(cfg_data_dir + '\\' + file, 'r') as actfile:
                file_content = actfile.read()
                parse_content(file_content)

    return 1


# get_files_from_web()
parse_files()

# print(page)
