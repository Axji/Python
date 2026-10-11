"""Zugriff auf die lokale SQLite-Wetterdatenbank (homogene Monatsdaten von MeteoSchweiz)."""
import os
import sqlite3

# Standardpfad der Datenbank: Unterordner "daten" neben diesem Skript
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'daten', 'weather.db')

# Messwerte im "langen" Format: eine Zeile je Station, Monat und Parameter. Die Parameter unterscheiden sich je Station,
# deshalb gibt es keine feste Spalte pro Messgrösse. Ein erneuter Abruf überschreibt den Wert und setzt retrieved_at neu.
SCHEMA = '''
CREATE TABLE IF NOT EXISTS homogeneous_monthly (
    station_abbr text NOT NULL,
    month_start text NOT NULL,      -- JJJJ-MM-TT, immer der Monatserste
    parameter text NOT NULL,        -- Kürzel, siehe Tabelle parameters
    value real NOT NULL,
    retrieved_at text NOT NULL,     -- Zeitpunkt des Abrufs, ISO 8601 (JJJJ-MM-TTTHH:MM:SS)
    PRIMARY KEY (station_abbr, month_start, parameter)
);
CREATE TABLE IF NOT EXISTS stations (
    station_abbr text PRIMARY KEY,
    station_name text,
    canton text,
    height_masl real,
    lat real,
    lon real,
    collection text,
    retrieved_at text
);
CREATE TABLE IF NOT EXISTS parameters (
    parameter text PRIMARY KEY,
    description_de text,
    description_en text,
    unit text,
    retrieved_at text
);
'''


class SqlLiteWD:
    """Schreibt Wetterdaten in die lokale SQLite-Datenbank und legt die Tabellen bei Bedarf an."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None

    def con_open(self):
        """Öffnet die Verbindung, falls noch keine besteht (Ordner und Tabellen werden angelegt), und gibt sie zurück."""
        if self.conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.executescript(SCHEMA)
        return self.conn

    def con_close(self):
        """Schliesst die Verbindung, falls sie offen ist."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def save_monthly(self, values, retrieved_at):
        """Speichert Messwerte als Liste von (Station, Monatserster, Parameter, Wert). Gibt die Anzahl zurück."""
        rows = [(station, month, parameter, value, retrieved_at) for station, month, parameter, value in values]
        conn = self.con_open()
        # Platzhalter (?) statt Textzusammenbau, damit keine SQL-Injection möglich ist
        conn.executemany("INSERT OR REPLACE INTO homogeneous_monthly VALUES (?,?,?,?,?)", rows)
        conn.commit()
        return len(rows)

    def save_stations(self, stations, retrieved_at):
        """Speichert Stationsdaten als Liste von (Kürzel, Name, Kanton, Höhe, Breite, Länge, Datensatz)."""
        conn = self.con_open()
        conn.executemany("INSERT OR REPLACE INTO stations VALUES (?,?,?,?,?,?,?,?)",
                         [tuple(s) + (retrieved_at,) for s in stations])
        conn.commit()

    def save_parameters(self, parameters, retrieved_at):
        """Speichert Parameterbeschreibungen als Liste von (Kürzel, Beschreibung de, Beschreibung en, Einheit)."""
        conn = self.con_open()
        conn.executemany("INSERT OR REPLACE INTO parameters VALUES (?,?,?,?,?)",
                         [tuple(p) + (retrieved_at,) for p in parameters])
        conn.commit()

    # Kontextmanager: `with SqlLiteWD() as db:` öffnet und schliesst die Verbindung automatisch
    def __enter__(self):
        self.con_open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.con_close()
