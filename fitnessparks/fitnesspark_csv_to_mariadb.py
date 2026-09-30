"""Importiert die CSV-Dateien der Fitnesspark-Auslastung in eine MariaDB-Tabelle.

Ablauf: Alle *.csv aus dem Ordner `files_to_import` werden eingelesen und in die Tabelle `besucher` geschrieben.
Benötigte Umgebungsvariable: FITNESS_DB_PASSWORD
Optional: FITNESS_DB_HOST (Standard 127.0.0.1), FITNESS_DB_USER (Standard fitnesspar), FITNESS_DB_NAME (Standard fitnessparks).
"""
import glob
import os
import sys

import pandas as pd
import pymysql

# Konfigurationsvariablen
# Zugangsdaten kommen aus Umgebungsvariablen und werden nie eingecheckt.
DB_HOST = os.environ.get('FITNESS_DB_HOST', '127.0.0.1')
DB_USER = os.environ.get('FITNESS_DB_USER', 'fitnesspar')
DB_NAME = os.environ.get('FITNESS_DB_NAME', 'fitnessparks')
TABLE_NAME = 'besucher'  # Zieltabelle
CSV_DIRECTORY = 'files_to_import'  # Ordner mit den zu importierenden CSV-Dateien
LOAD_USER = 'PythonScript'  # Benutzer, der den Ladevorgang durchführt


def load_csv_to_mariadb(csv_dir, table_name, db_conn, load_user):
    """
    Liest alle CSV-Dateien aus einem Verzeichnis und fügt sie in eine MariaDB-Tabelle ein.
    Jede Datei wird in einer eigenen Transaktion geladen: Ein Fehler in einer Datei
    macht nur diese Datei rückgängig, bereits geladene Dateien bleiben erhalten.
    """
    files = glob.glob(os.path.join(csv_dir, '*.csv'))
    if not files:
        print(f"Keine CSV-Dateien im Verzeichnis '{csv_dir}' gefunden.")
        return

    print(f"{len(files)} CSV-Dateien zum Verarbeiten gefunden.")

    # Platzhalter (%s) statt Textzusammenbau, damit keine SQL-Injection möglich ist
    sql = (
        f"INSERT INTO `{table_name}` "
        "(`fitnesspark`, `belegung`, `Timestamp`, `loaduser`) "
        "VALUES (%s, %s, %s, %s)"
    )

    total_rows_inserted = 0
    with db_conn.cursor() as cursor:
        for file in files:
            print(f"Verarbeite Datei: {file}")
            try:
                df = pd.read_csv(file)
                # Sicherstellen, dass die Datei die erwarteten drei Spalten hat, und sie passend zur Tabelle benennen
                if len(df.columns) != 3:
                    raise ValueError(f"3 Spalten erwartet, gefunden: {len(df.columns)}")
                df.columns = ['fitnesspark', 'belegung', 'Timestamp']

                # Zeilen in Tupel umwandeln und Datentypen absichern (Text, Ganzzahl, Zeitstempel)
                rows = [
                    (
                        str(row.fitnesspark),
                        int(row.belegung),
                        pd.Timestamp(row.Timestamp).to_pydatetime(),
                        load_user,
                    )
                    for row in df.itertuples(index=False)
                ]

                cursor.executemany(sql, rows)  # Alle Zeilen der Datei in einem Schritt einfügen
                db_conn.commit()
                total_rows_inserted += len(rows)
                print(f"   -> {len(rows)} Zeilen erfolgreich eingefügt.")
            except Exception as e:
                print(f"   Fehler beim Verarbeiten von Datei {file}: {e}")
                db_conn.rollback()  # Nur diese Datei rückgängig machen

    print(f"\nLadevorgang abgeschlossen. {total_rows_inserted} Zeilen insgesamt eingefügt.")


def main():
    """
    Hauptfunktion zur Steuerung des Skripts.
    """
    # Das Passwort kommt nur aus der Umgebung und steht nie im Code
    password = os.environ.get('FITNESS_DB_PASSWORD')
    if not password:
        sys.exit("Umgebungsvariable FITNESS_DB_PASSWORD ist nicht gesetzt.")

    print("Starte den Ladevorgang...")

    connection = None  # Vorab setzen, damit `finally` auch nach einem Verbindungsfehler funktioniert
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=password,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        print("Verbindung zur MariaDB erfolgreich hergestellt.")
        load_csv_to_mariadb(CSV_DIRECTORY, TABLE_NAME, connection, LOAD_USER)

    except pymysql.MySQLError as e:
        print(f"Fehler bei der Datenbankverbindung: {e}")
    finally:
        if connection is not None and connection.open:
            connection.close()
            print("Verbindung zur MariaDB geschlossen.")


if __name__ == "__main__":
    main()
