"""Importiert CSV-Dateien der Fitnesspark-Auslastung in die SQLite-Datenbank.

Ablauf: Alle *.csv aus dem Ordner `data` werden eingelesen und in die Tabelle `besucher` geschrieben. Das ist
nützlich, um ältere CSV-Dateien nachträglich zu laden. Die Datenbank (data/fitnessparks.db) wird mit Ordner und
Tabelle automatisch angelegt, es wird kein Datenbankserver und kein Passwort benötigt. Bereits vorhandene Zeilen
werden übersprungen, der Import kann also gefahrlos wiederholt werden. Es werden keine Zusatzpakete benötigt.
"""
import csv
import datetime as dt
import glob
import os
import sqlite3
import sys

# Das gemeinsame Datenbankmodul liegt eine Ebene höher
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fitnesspark_db  # noqa: E402

LOAD_USER = 'PythonScript'  # Benutzer, der den Ladevorgang durchführt


def read_csv_rows(file, load_user):
    """
    Liest eine CSV-Datei (Kopfzeile, danach je Zeile: Park, Belegung, Zeitstempel) und gibt die Zeilen als Tupel
    für die Datenbank zurück. Bei einer fehlerhaften Zeile wird ein ValueError mit der Zeilennummer ausgelöst.
    """
    rows = []
    with open(file, newline='', encoding='utf-8-sig') as csvfile:  # utf-8-sig entfernt ein evtl. vorhandenes BOM
        reader = csv.reader(csvfile)
        next(reader, None)  # Kopfzeile überspringen
        for line_number, row in enumerate(reader, start=2):
            if not row:  # Leerzeilen ignorieren
                continue
            # Sicherstellen, dass die Zeile die erwarteten drei Spalten hat
            if len(row) != 3:
                raise ValueError(f"Zeile {line_number}: 3 Spalten erwartet, gefunden: {len(row)}")
            park, belegung, timestamp = row
            try:
                # Datentypen absichern: Text, Ganzzahl und Zeitstempel als ISO-Text mit Leerzeichen
                rows.append((
                    park,
                    int(float(belegung)),
                    dt.datetime.fromisoformat(timestamp).isoformat(sep=' '),
                    load_user,
                ))
            except ValueError as e:
                raise ValueError(f"Zeile {line_number}: ungültiger Wert ({e})") from e
    return rows


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
            rows = read_csv_rows(file, load_user)
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
