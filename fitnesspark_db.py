"""Gemeinsamer SQLite-Zugriff für die Fitnesspark-Skripte.

Die Datenbank und die CSV-Sicherungen liegen im Ordner `data` neben diesem Modul. Der Ordner, die Datenbankdatei
und die Tabelle werden bei Bedarf automatisch angelegt.
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')  # Ordner für Datenbank und CSV-Dateien
DB_PATH = os.path.join(DATA_DIR, 'fitnessparks.db')
TABLE_NAME = 'besucher'  # Zieltabelle


def open_database(db_path=DB_PATH):
    """
    Öffnet die Datenbank und stellt sicher, dass Ordner, Datei und Tabelle existieren.
    Die Kombination aus Fitnesspark und Zeitstempel ist eindeutig, so entstehen beim erneuten
    Import derselben Daten keine doppelten Zeilen.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Datenordner anlegen, falls er fehlt
    conn = sqlite3.connect(db_path)  # Legt die Datenbankdatei beim ersten Zugriff an
    with conn:
        conn.execute(
            f'CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" ('
            "fitnesspark TEXT NOT NULL, "
            "belegung INTEGER NOT NULL, "
            "Timestamp TEXT NOT NULL, "
            "loaduser TEXT, "
            "UNIQUE (fitnesspark, Timestamp))"
        )
    return conn


def insert_rows(conn, rows):
    """
    Fügt Zeilen der Form (fitnesspark, belegung, Timestamp, loaduser) in einer Transaktion ein.
    Bereits vorhandene Zeilen werden übersprungen. Gibt die Anzahl neu eingefügter Zeilen zurück.
    Bei einem Fehler wird die gesamte Transaktion rückgängig gemacht.
    """
    # Platzhalter (?) statt Textzusammenbau, damit keine SQL-Injection möglich ist
    sql = (
        f'INSERT OR IGNORE INTO "{TABLE_NAME}" '
        "(fitnesspark, belegung, Timestamp, loaduser) VALUES (?, ?, ?, ?)"
    )
    with conn:  # Bestätigt bei Erfolg, macht bei einem Fehler rückgängig
        before = conn.total_changes
        conn.executemany(sql, rows)
        return conn.total_changes - before
