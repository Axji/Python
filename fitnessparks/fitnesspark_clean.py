"""Bereinigt die SQLite-Datenbank: Aufeinanderfolgende Zeilen mit gleichem Wert werden bis auf die erste gelöscht.

Pro Fitnesspark werden die Messungen nach Zeitstempel sortiert. Hat eine Messung dieselbe Belegung wie die
unmittelbar vorherige Messung desselben Parks, unterscheidet sie sich nur im Zeitstempel und wird gelöscht. Von
jeder Folge gleicher Werte bleibt also nur die erste Zeile übrig. Ändert sich der Wert später, bleibt diese Zeile
erhalten, auch wenn derselbe Wert schon früher einmal vorkam (A, A, B, A, A wird zu A, B, A).

Die CSV-Sicherungen werden nicht verändert. Mit --dry-run wird nur angezeigt, was gelöscht würde.
Mit --since JJJJ-MM-TT werden nur Zeilen ab diesem Tag bereinigt (ältere Zeilen bleiben unberührt, dienen aber als
Vergleichswert für die erste Zeile ab dem Stichtag). Das Ergebnis ist dasselbe wie bei einer vollständigen Bereinigung,
wenn der Rest der Datenbank schon bereinigt war.

Aufruf:  py fitnesspark_clean.py [--dry-run] [--since JJJJ-MM-TT]
"""
import argparse
import datetime as dt
import os
import sqlite3
import sys

# Das gemeinsame Datenbankmodul liegt eine Ebene höher
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fitnesspark_db  # noqa: E402

# Zeilen, deren Belegung der vorherigen Zeile desselben Parks entspricht (LAG = Wert der vorherigen Zeile).
# Die Teilabfrage wird vor dem Löschen vollständig ausgewertet, die Folgen werden also korrekt erkannt.
DUPLICATE_ROWS = f"""
    SELECT rowid FROM (
        SELECT rowid, belegung,
               LAG(belegung) OVER (PARTITION BY fitnesspark ORDER BY Timestamp, rowid) AS vorherige
        FROM "{fitnesspark_db.TABLE_NAME}"
    )
    WHERE belegung = vorherige
"""


# Wie DUPLICATE_ROWS, aber nur für Zeilen ab dem Stichtag (?). Als Vergleichswert wird pro Park zusätzlich die letzte
# Zeile vor dem Stichtag mitgelesen, damit die erste Zeile ab dem Stichtag richtig beurteilt wird.
DUPLICATE_ROWS_SINCE = f"""
    SELECT rowid FROM (
        SELECT rowid, Timestamp, belegung,
               LAG(belegung) OVER (PARTITION BY fitnesspark ORDER BY Timestamp, rowid) AS vorherige
        FROM "{fitnesspark_db.TABLE_NAME}"
        WHERE Timestamp >= :since OR rowid IN (
            SELECT (SELECT b.rowid FROM "{fitnesspark_db.TABLE_NAME}" b
                    WHERE b.fitnesspark = p.fitnesspark AND b.Timestamp < :since
                    ORDER BY b.Timestamp DESC, b.rowid DESC LIMIT 1)
            FROM (SELECT DISTINCT fitnesspark FROM "{fitnesspark_db.TABLE_NAME}") p
        )
    )
    WHERE belegung = vorherige AND Timestamp >= :since
"""


def clean(db_conn, dry_run, since=None):
    """
    Löscht die überflüssigen Folgezeilen und gibt (Zeilen vorher, gelöscht) zurück.
    Bei `dry_run` wird nichts verändert, es wird nur gezählt.
    Mit `since` (JJJJ-MM-TT) werden nur Zeilen ab diesem Tag geprüft.
    """
    table = fitnesspark_db.TABLE_NAME
    duplicates = DUPLICATE_ROWS_SINCE if since else DUPLICATE_ROWS
    params = {"since": since} if since else {}
    total = db_conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    to_delete = db_conn.execute(f"SELECT COUNT(*) FROM ({duplicates})", params).fetchone()[0]
    if not dry_run and to_delete:
        with db_conn:  # Eine Transaktion: bei einem Fehler wird nichts gelöscht
            db_conn.execute(f'DELETE FROM "{table}" WHERE rowid IN ({duplicates})', params)
    return total, to_delete


def main():
    """
    Hauptfunktion zur Steuerung des Skripts.
    """
    parser = argparse.ArgumentParser(description="Entfernt aufeinanderfolgende Zeilen mit gleichem Wert.")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, was gelöscht würde.")
    parser.add_argument("--since", metavar="JJJJ-MM-TT",
                        help="Nur Zeilen ab diesem Tag bereinigen (Standard: die ganze Datenbank).")
    args = parser.parse_args()
    if args.since:
        dt.date.fromisoformat(args.since)  # Fehler bei ungültigem Datum, bevor etwas gelöscht wird

    # Die Datenbank nicht versehentlich neu anlegen, wenn es noch keine gibt
    if not os.path.exists(fitnesspark_db.DB_PATH):
        sys.exit(f"Keine Datenbank gefunden: {fitnesspark_db.DB_PATH}")

    connection = sqlite3.connect(fitnesspark_db.DB_PATH)
    try:
        total, deleted = clean(connection, args.dry_run, args.since)
        if args.dry_run:
            print(f"Testlauf: {deleted} von {total} Zeilen würden gelöscht, {total - deleted} blieben übrig.")
        else:
            print(f"{deleted} von {total} Zeilen gelöscht, {total - deleted} Zeilen übrig.")
            if deleted:
                connection.execute("VACUUM")  # Freigewordenen Speicherplatz zurückgeben
    except sqlite3.Error as e:
        sys.exit(f"Fehler bei der Bereinigung: {e}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
