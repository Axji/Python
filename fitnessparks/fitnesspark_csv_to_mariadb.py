import os
import pandas as pd
import pymysql
from pymysql.converters import escape_string
import glob

# Konfigurationsvariablen
DB_HOST = '127.0.0.1'
DB_USER = 'fitnesspar'
DB_PASSWORD = 'fitness+Qayxsw2'
DB_NAME = 'fitnessparks'
TABLE_NAME = 'besucher'
CSV_DIRECTORY = 'files_to_import'
LOAD_USER = 'PythonScript'  # Benutzer, der den Ladevorgang durchführt


def load_csv_to_mariadb(csv_dir, table_name, db_conn, load_user):
    """
    Liest alle CSV-Dateien aus einem Verzeichnis und fügt sie in eine MariaDB-Tabelle ein.
    """
    files = glob.glob(os.path.join(csv_dir, '*.csv'))
    if not files:
        print(f"Keine CSV-Dateien im Verzeichnis '{csv_dir}' gefunden.")
        return

    print(f"{len(files)} CSV-Dateien zum Verarbeiten gefunden.")

    total_rows_inserted = 0
    with db_conn.cursor() as cursor:
        for file in files:
            print(f"Verarbeite Datei: {file}")
            try:
                # Lesen der CSV-Datei in einen Pandas DataFrame
                df = pd.read_csv(file)
                # Sicherstellen, dass die Spaltennamen mit der Tabelle übereinstimmen
                df.columns = ['fitnesspark', 'belegung', 'Timestamp']

                # Daten in MariaDB einfügen
                # Erstellen der SQL-INSERT-Anweisung
                for index, row in df.iterrows():
                    fitnesspark = escape_string(str(row['fitnesspark']))
                    belegung = int(row['belegung'])
                    timestamp = row['Timestamp']

                    sql = f"""
                    INSERT INTO `{table_name}`
                    (`fitnesspark`, `belegung`, `Timestamp`, `loaduser`)
                    VALUES
                    ('{fitnesspark}', {belegung}, '{timestamp}', '{load_user}')
                    """
                    cursor.execute(sql)
                    total_rows_inserted += 1

                print(f"   -> {len(df)} Zeilen erfolgreich eingefügt.")
            except Exception as e:
                print(f"   Fehler beim Verarbeiten von Datei {file}: {e}")
                db_conn.rollback()  # Rückgängig machen der Transaktion bei Fehler

    db_conn.commit()  # Speichern der Transaktion
    print(f"\nDatenbank-Transaktion abgeschlossen. {total_rows_inserted} Zeilen insgesamt eingefügt.")


def main():
    """
    Hauptfunktion zur Steuerung des Skripts.
    """
    print("Starte den Ladevorgang...")

    try:
        # Verbindung zur MariaDB-Datenbank herstellen
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        print("Verbindung zur MariaDB erfolgreich hergestellt.")

        # Funktion zum Laden der Daten aufrufen
        load_csv_to_mariadb(CSV_DIRECTORY, TABLE_NAME, connection, LOAD_USER)

    except pymysql.MySQLError as e:
        print(f"Fehler bei der Datenbankverbindung: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Verbindung zur MariaDB geschlossen.")


if __name__ == "__main__":
    main()