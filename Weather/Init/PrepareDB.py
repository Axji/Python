"""Legt die SQLite-Datenbank und ihre Tabellen für die Wetterdaten an (gefahrlos mehrfach ausführbar).

GetWeatherData.py legt die Tabellen bei Bedarf selbst an; dieses Skript ist nur für das Vorbereiten ohne Abruf.
"""
import os
import sys

# Das Skript liegt in Init/, die Datenbankklasse eine Ebene höher
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from SqlLiteWD import SqlLiteWD  # noqa: E402  (erst nach dem Anpassen von sys.path möglich)

with SqlLiteWD() as db:
    print("Datenbank bereit: " + db.db_path)
