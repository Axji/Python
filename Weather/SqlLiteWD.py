"""Zugriff auf die lokale SQLite-Wetterdatenbank."""
import datetime
import os
import sqlite3

# Standardpfad der Datenbank: Unterordner "daten" neben diesem Skript
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'daten', 'weather.db')


class SqlLiteWD:
    """Schreibt Wetterdaten in die lokale SQLite-Datenbank (Tabelle wird von Init/PrepareDB.py angelegt)."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None

    def con_open(self):
        """Öffnet die Verbindung, falls noch keine besteht, und gibt sie zurück."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def con_close(self):
        """Schliesst die Verbindung, falls sie offen ist."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def insert_weather_data(self, station, year, month, temp, rain, create_user='system', create_date=None,
                            update_user='system', update_date=None):
        """Fügt einen Datensatz (Station, Jahr, Monat, Temperatur, Niederschlag) in die Tabelle `weather` ein.

        Fehlende Erstell- und Änderungszeitpunkte werden mit der aktuellen Zeit gefüllt.
        """
        now = datetime.datetime.now()
        weather_line = [station, year, month, temp, rain,
                        create_user, create_date or now, update_user, update_date or now]
        conn = self.con_open()
        # Platzhalter (?) statt Textzusammenbau, damit keine SQL-Injection möglich ist
        conn.execute("INSERT INTO weather VALUES (?,?,?,?,?,?,?,?,?)", weather_line)
        conn.commit()

    # Kontextmanager: `with SqlLiteWD() as db:` öffnet und schliesst die Verbindung automatisch
    def __enter__(self):
        self.con_open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.con_close()
