"""Importiert die CSV-Dateien der Fitnesspark-Auslastung in eine lokale SQLite-Datenbank.

Ablauf: Alle *.csv aus dem Ordner `files_to_import` werden eingelesen und in die Tabelle `besucher` geschrieben.
Die Datenbank ist eine einzelne Datei (Standard: fitnessparks.db neben diesem Skript). Es wird weder ein
Datenbankserver noch ein Passwort benötigt. Optional kann mit der Umgebungsvariable FITNESS_DB_PATH ein anderer
Pfad vorgegeben werden.
"""
import glob
import os
import sqlite3

import pandas as pd

# Konfigurationsvariablen
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('FITNESS_DB_PATH', os.path.join(BASE_DIR, 'fitnessparks.db'))
TABLE_NAME = 'besucher'  # Zieltabelle
CSV_DIRECTORY = os.path.join(BASE_DIR, 'files_to_import')  # Ordner mit den zu importierenden CSV-Dateien
LOAD_USER = 'PythonScript'  # Benutzer, der den Ladevorgang durchführt


def create_table_if_not_exists(db_conn, table_name):
    """
    Legt die Zieltabelle an, falls sie noch nicht existiert.
    Die Kombination aus Fitnesspark und Zeitstempel ist eindeutig, so entstehen beim erneuten
    Import derselben Datei keine doppelten Zeilen.
    """
    with db_conn:
        db_conn.execute(
            f'CREATE TABLE IF NOT EXISTS "{table_name}" ('
            "fitnesspark TEXT NOT NULL, "
            "belegung INTEGER NOT NULL, "
            "Timestamp TEXT NOT NULL, "
            "loaduser TEXT, "
            "UNIQUE (fitnesspark, Timestamp))"
        )


def load_csv_to_sqlite(csv_dir, table_name, db_conn, load_user):
    """
    Liest alle CSV-Dateien aus einem Verzeichnis und fügt sie in eine SQLite-Tabelle ein.
    Jede Datei wird in einer eigenen Transaktion geladen: Ein Fehler in einer Datei
    macht nur diese Datei rückgängig, bereits geladene Dateien bleiben erhalten.
    """
    files = glob.glob(os.path.join(csv_dir, '*.csv'))
    if not files:
        print(f"Keine CSV-Dateien im Verzeichnis '{csv_dir}' gefunden.")
        return

    print(f"{len(files)} CSV-Dateien zum Verarbeiten gefunden.")

    # Platzhalter (?) statt Textzusammenbau, damit keine SQL-Injection möglich ist.
    # OR IGNORE überspringt Zeilen, die schon in der Tabelle stehen (siehe UNIQUE-Bedingung).
    sql = (
        f'INSERT OR IGNORE INTO "{table_name}" '
        "(fitnesspark, belegung, Timestamp, loaduser) "
        "VALUES (?, ?, ?, ?)"
    )

    total_rows_inserted = 0
    for file in files:
        print(f"Verarbeite Datei: {file}")
        try:
            df = pd.read_csv(file)
            # Sicherstellen, dass die Datei die erwarteten drei Spalten hat, und sie passend zur Tabelle benennen
            if len(df.columns) != 3:
                raise ValueError(f"3 Spalten erwartet, gefunden: {len(df.columns)}")
            df.columns = ['fitnesspark', 'belegung', 'Timestamp']

            # Zeilen in Tupel umwandeln und Datentypen absichern (Text, Ganzzahl, Zeitstempel als ISO-Text)
            rows = [
                (
                    str(row.fitnesspark),
                    int(row.belegung),
                    pd.Timestamp(row.Timestamp).isoformat(sep=' '),
                    load_user,
                )
                for row in df.itertuples(index=False)
            ]

            # `with db_conn` bestätigt die Transaktion bei Erfolg und macht sie bei einem Fehler rückgängig
            with db_conn:
                before = db_conn.total_changes
                db_conn.executemany(sql, rows)  # Alle Zeilen der Datei in einem Schritt einfügen
                inserted = db_conn.total_changes - before
            total_rows_inserted += inserted
            print(f"   -> {inserted} Zeilen erfolgreich eingefügt ({len(rows) - inserted} bereits vorhanden).")
        except Exception as e:
            print(f"   Fehler beim Verarbeiten von Datei {file}: {e}")

    print(f"\nLadevorgang abgeschlossen. {total_rows_inserted} Zeilen insgesamt eingefügt.")


def main():
    """
    Hauptfunktion zur Steuerung des Skripts.
    """
    print("Starte den Ladevorgang...")

    connection = None  # Vorab setzen, damit `finally` auch nach einem Verbindungsfehler funktioniert
    try:
        # Die Datenbankdatei wird beim ersten Zugriff automatisch angelegt
        connection = sqlite3.connect(DB_PATH)
        print(f"Verbindung zur SQLite-Datenbank '{DB_PATH}' erfolgreich hergestellt.")
        create_table_if_not_exists(connection, TABLE_NAME)
        load_csv_to_sqlite(CSV_DIRECTORY, TABLE_NAME, connection, LOAD_USER)

    except sqlite3.Error as e:
        print(f"Fehler bei der Datenbankverbindung: {e}")
    finally:
        if connection is not None:
            connection.close()
            print("Verbindung zur Datenbank geschlossen.")


if __name__ == "__main__":
    main()
