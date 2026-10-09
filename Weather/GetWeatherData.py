"""Lädt Klimadaten (Monatswerte) von MeteoSchweiz herunter und liest sie aus.

Ablauf: `get_files_from_web()` speichert pro Station eine Textdatei im Datenordner (Dateiname: Datum_Station.txt),
`parse_files()` wertet die Dateien des neuesten Datums aus. Die Einstellungen stehen in config.ini
(erzeugt von Init/Config_Generator.py).
"""
import configparser
import datetime
import os
import re
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Konfiguration aus config.ini neben diesem Skript lesen
config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'config.ini'), encoding='utf-8')
cfg_data_dir = os.path.join(BASE_DIR, config['DEFAULT']['dataDir'])
debugLevel = 3  # Meldungen mit höherer Stufe als dieser Wert werden nicht ausgegeben
REQUEST_TIMEOUT = 30  # Sekunden
# Gültige Dateinamen: JJJJ-MM-TT_Station.txt
DATA_FILE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}_.+\.txt$')


def debug_print(debug_text, debug_lvl):
    """Gibt eine Meldung mit vorangestelltem Marker auf der Konsole aus, wenn die Debug-Stufe ausreicht."""
    if debugLevel < debug_lvl:
        return
    print("### - " + debug_text[:500])  # Auf 500 Zeichen kürzen, damit grosse Dateiinhalte die Konsole nicht fluten


def get_files_from_web():
    """Lädt für jede Station aus `wetter_stations` die aktuellen Wetterdaten herunter und speichert sie im Datenordner."""
    debug_print("get_files_from_web()",1)

    # Kürzel der Messstationen, die abgerufen werden
    wetter_stations = ['SIO', 'BER', 'BAS', 'CHM', 'CHD', 'GSB',
                       'DAV', 'ENG', 'GVE', 'LUG', 'PAY', 'SIA',
                       'SAE', 'SMA']
    cfg_base_url = config['DEFAULT']['baseUrl']
    cfg_string_to_replace_in_url = config['DEFAULT']['stringToReplaceInUrl']
    cfg_sleep_time_between_files = int(config['DEFAULT']['sleepTimeBetweenFiles'])

    date_start = datetime.date.today().isoformat()
    for wetter_station in wetter_stations:
        # Stationskürzel in die Basis-Adresse einsetzen
        actual_url = cfg_base_url.replace(cfg_string_to_replace_in_url, wetter_station)
        print("Actual File =" + actual_url)

        req = urllib.request.Request(actual_url)
        # Eigener User-Agent, damit der Server den Zugriff zuordnen kann
        req.add_header('User-Agent', 'urllib-example/0.1 (Contact: . . .)')

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            html_content = response.read().decode('utf-8', errors='replace')

        # Zeilenenden vereinheitlichen und doppelte Leerzeilen entfernen (zweimal, da "\n\n\n" sonst übrig bleibt)
        html_content = html_content.replace("\r\n", "\n")
        html_content = html_content.replace("\n\n", "\n")
        html_content = html_content.replace("\n\n", "\n")

        # Datei als Datum_Station.txt speichern
        os.makedirs(cfg_data_dir, exist_ok=True)
        target = os.path.join(cfg_data_dir, date_start + '_' + wetter_station + '.txt')
        with open(target, 'w', encoding='utf-8') as f:
            f.write(html_content)
        time.sleep(cfg_sleep_time_between_files)  # Pause zwischen den Downloads


def get_date_from_file(file):
    """Liest das Datum aus dem Dateinamen (die ersten 10 Zeichen, Format JJJJ-MM-TT)."""
    debug_print("get_date_from_file("+file+")", 1)

    datestring = file[:10]
    extracteddate = datetime.datetime.strptime(datestring, '%Y-%m-%d').date()
    debug_print("Extracted Date " + extracteddate.strftime('%Y-%m-%d'), 3)
    return extracteddate


def parse_content(filecontent):
    """Liest den Stationsnamen und die Messwerte aus dem Dateiinhalt.

    Das Schreiben in die Datenbank ist noch nicht umgesetzt (siehe auskommentierten Entwurf unten).
    """
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
    # Der Stationsname steht hinter mehreren Leerzeichen in der Stationszeile
    station = station_line[str.find(station_line, "    "):].strip()
    debug_print(station, 4)

    debug_print(filecontent[data_pos:], 4)

    # Noch nicht umgesetzt: Schreiben in die Datenbank (Zugangsdaten aus Umgebungsvariablen lesen,
    # Treiber "ODBC Driver 18 for SQL Server" verwenden; pyodbc dann in requirements.txt aufnehmen).
    # conn = pyodbc.connect(conn_str)
    # conn.autocommit = True
    #
    # cursor = conn.cursor()
    #
    # baseSQL = """INSERT INTO [Landing_Weather]
    #     ([Station] ,[Jahr] ,[Monat] ,[Temp] ,[Rain] ,[loaddate])
    #     VALUES (?,?,?,?,?,?);"""
    #
    # #baseSQL = """  INSERT INTO [dbo].[Landing_Weather] ([Station] ,[Jahr] ,[Monat] ,[Temp] ,[Rain] ,[loaddate]) VALUES ('A',1980,5,14,0,'2021-04-27')"""
    #
    # for line in filecontent[data_pos:].split("\n"):
    #     if len(line) > 20:
    #         year = int(line[0:4])
    #         month = int(line[9:11])
    #         temp = -999.9
    #         rain = -999.9
    #         if line[25:30] != '   NA':
    #             temp = float(line[25:30])
    #         if line[44:49] != '   NA':
    #             rain = float(line[44:49])
    #
    #         cursor.execute(baseSQL, (station, year, month, temp, rain, datetime.datetime.now()))

    return 0


def parse_files():
    """Liest alle Dateien aus dem Datenverzeichnis und wertet die Dateien mit dem neuesten Datum aus."""
    # Startwert weit in der Vergangenheit, damit jede echte Datei neuer ist
    max_date = datetime.datetime.strptime('1980-05-14', '%Y-%m-%d').date()
    file_list = [f for f in os.listdir(cfg_data_dir) if DATA_FILE_PATTERN.match(f)]
    for file in file_list:
        file_date = get_date_from_file(file)
        if file_date > max_date:
            max_date = file_date

    # Nur die Dateien vom neuesten Datum verarbeiten
    for file in file_list:
        if file.startswith(max_date.isoformat()):
            with open(os.path.join(cfg_data_dir, file), encoding='utf-8', errors='replace') as actfile:
                file_content = actfile.read()
                parse_content(file_content)

    return 1


if __name__ == "__main__":
    # Download ist standardmässig ausgeschaltet; zum Aktualisieren der Daten einkommentieren
    # get_files_from_web()
    parse_files()
