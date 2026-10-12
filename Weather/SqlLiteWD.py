"""Zugriff auf die lokale SQLite-Wetterdatenbank (homogene Monatsdaten von MeteoSchweiz)."""
import os
import sqlite3

# Standardpfad der Datenbank: Unterordner "daten" neben diesem Skript
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'daten', 'weather.db')

# Messwerte im "langen" Format: eine Zeile je Station, Monat und Parameter. Die Parameter unterscheiden sich je Station,
# deshalb gibt es keine feste Spalte pro Messgrösse. Ein erneuter Abruf überschreibt den Wert.
# Platzsparend gebaut (zusammen etwa halb so gross): WITHOUT ROWID speichert den Primärschlüssel nicht noch einmal als Index,
# und der Abrufzeitpunkt steht einmal in der Tabelle meta (er ist für alle Zeilen eines Abrufs gleich), nicht in jeder Zeile.
SCHEMA = '''
CREATE TABLE IF NOT EXISTS homogeneous_monthly (
    station_abbr text NOT NULL,
    month_start text NOT NULL,      -- JJJJ-MM-TT, immer der Monatserste
    parameter text NOT NULL,        -- sprechender Name, siehe Tabelle parameters
    value real NOT NULL,
    PRIMARY KEY (station_abbr, month_start, parameter)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS meta (
    key text PRIMARY KEY,
    value text                      -- monthly_retrieved_at: Zeitpunkt des letzten Abrufs, ISO 8601 (JJJJ-MM-TTTHH:MM:SS)
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
    parameter text PRIMARY KEY,     -- sprechender Name, siehe ParameterNames.py
    code text,                      -- Originalkürzel von MeteoSchweiz
    description_de text,
    description_en text,
    unit text,
    retrieved_at text
);
'''


def migrate_monthly(conn):
    """Baut eine ältere Datenbank um: Die Tabelle homogeneous_monthly hatte noch retrieved_at in jeder Zeile."""
    columns = [row[1] for row in conn.execute("PRAGMA table_info(homogeneous_monthly)")]
    if 'retrieved_at' not in columns:
        return
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('monthly_retrieved_at', (SELECT max(retrieved_at) FROM homogeneous_monthly))")
    conn.execute("ALTER TABLE homogeneous_monthly RENAME TO homogeneous_monthly_old")
    conn.executescript(SCHEMA)  # legt die neue Tabelle an (die übrigen Tabellen existieren schon)
    conn.execute("INSERT INTO homogeneous_monthly SELECT station_abbr, month_start, parameter, value FROM homogeneous_monthly_old")
    conn.execute("DROP TABLE homogeneous_monthly_old")
    conn.commit()
    conn.execute("VACUUM")  # gibt den frei gewordenen Platz an das Dateisystem zurück


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
            migrate_monthly(self.conn)
        return self.conn

    def con_close(self):
        """Schliesst die Verbindung, falls sie offen ist."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def save_monthly(self, values, retrieved_at):
        """Speichert Messwerte als Liste von (Station, Monatserster, Parameter, Wert). Gibt die Anzahl zurück."""
        rows = list(values)
        conn = self.con_open()
        # Platzhalter (?) statt Textzusammenbau, damit keine SQL-Injection möglich ist
        conn.executemany("INSERT OR REPLACE INTO homogeneous_monthly VALUES (?,?,?,?)", rows)
        conn.execute("INSERT OR REPLACE INTO meta VALUES ('monthly_retrieved_at', ?)", (retrieved_at,))
        conn.commit()
        return len(rows)

    def save_stations(self, stations, retrieved_at):
        """Speichert Stationsdaten als Liste von (Kürzel, Name, Kanton, Höhe, Breite, Länge, Datensatz)."""
        conn = self.con_open()
        conn.executemany("INSERT OR REPLACE INTO stations VALUES (?,?,?,?,?,?,?,?)",
                         [tuple(s) + (retrieved_at,) for s in stations])
        conn.commit()

    def save_parameters(self, parameters, retrieved_at):
        """Speichert Parameterbeschreibungen als Liste von (Name, Originalkürzel, Beschreibung de, Beschreibung en, Einheit)."""
        conn = self.con_open()
        conn.executemany("INSERT OR REPLACE INTO parameters VALUES (?,?,?,?,?,?)",
                         [tuple(p) + (retrieved_at,) for p in parameters])
        conn.commit()

    # Kontextmanager: `with SqlLiteWD() as db:` öffnet und schliesst die Verbindung automatisch
    def __enter__(self):
        self.con_open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.con_close()
