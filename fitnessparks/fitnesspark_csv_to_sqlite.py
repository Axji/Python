"""Importiert CSV-Dateien der Fitnesspark-Auslastung in die SQLite-Datenbank.

Ablauf: Alle *.csv aus dem Ordner `data` werden eingelesen und in die Tabelle `besucher` geschrieben. Das ist
nützlich, um ältere CSV-Dateien nachträglich zu laden. Die Datenbank (data/fitnessparks.db) wird mit Ordner und
Tabelle automatisch angelegt, es wird kein Datenbankserver und kein Passwort benötigt. Bereits vorhandene Zeilen
werden übersprungen, der Import kann also gefahrlos wiederholt werden.
"""
import glob
import os
import sqlite3
import sys

import pandas as pd

# Das gemeinsame Datenbankmodul liegt eine Ebene höher
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fitnesspark_db  # noqa: E402

LOAD_USER = 'PythonScript'  # Benutzer, der den Ladevorgang durchführt


def load_csv_to_sqlite(csv_dir, db_conn, load_user):
    """
    Liest alle CSV-Dateien aus einem Verzeichnis und fügt sie in die SQLite-Tabelle ein.
    Jede Datei wird in einer eigenen Transaktion geladen: Ein Fehler in einer Datei
    macht nur diese Datei rückgängig, bereits geladene Dateien bleiben erhalten.
    """
    files = glob.glob(os.path.join(csv_dir, '*.csv'))
    if not files:
        print(f"Keine CSV-Dateien im Verzeichnis '{csv_dir}' gefunden.")
        return

    print(f"{len(files)} CSV-Dateien zum Verarbeiten gefunden.")

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

            inserted = fitnesspark_db.insert_rows(db_conn, rows)
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
        # Legt Datenordner, Datenbankdatei und Tabelle bei Bedarf an
        connection = fitnesspark_db.open_database()
        print(f"Verbindung zur SQLite-Datenbank '{fitnesspark_db.DB_PATH}' erfolgreich hergestellt.")
        load_csv_to_sqlite(fitnesspark_db.DATA_DIR, connection, LOAD_USER)

    except sqlite3.Error as e:
        print(f"Fehler bei der Datenbankverbindung: {e}")
    finally:
        if connection is not None:
            connection.close()
            print("Verbindung zur Datenbank geschlossen.")


if __name__ == "__main__":
    main()
