import sqlite3
import datetime


class SqlLiteWD:
    conn = sqlite3.connect('..\daten\weather.db')
    isConnOpen = 0

    @staticmethod
    def insert_weather_data(station, year, month, temp, rain, create_user='system', create_date=datetime.datetime.now(),
                            update_user='system', update_date=datetime.datetime.now()):
        global conn
        global isConnOpen
        now = datetime.datetime.now()
        if isConnOpen == 0:
            con_open()
            c = conn.cursor()
            isConnOpen = 1
        weather_line = [station, year, month, temp, rain, create_user, create_date, update_user, update_date]
        c.execute("INSERT INTO weather VALUES (?,?,?,?,?,?,?,?,?)", weather_line)
        conn.commit()

    @staticmethod
    def con_close():
        global isConnOpen
        conn.close()
        isConnOpen = 0

    @staticmethod
    def con_open():
        global conn
        conn = sqlite3.connect('..\daten\weather.db')






