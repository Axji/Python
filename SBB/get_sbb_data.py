"""Lädt die Ist-Daten der SBB (data.sbb.ch, Datensatz ist-daten-sbb: Soll/Ist der Abfahrts- und Ankunftszeiten des Vortags)
und speichert sie als CSV-Datei pro Betriebstag in daten/ist_daten_JJJJMMTT.csv.

Der Datensatz enthält immer nur den Vortag. Die Historie entsteht, indem dieses Skript täglich läuft.
Gespeichert werden nur die Spalten, die für die Pünktlichkeitsauswertung nötig sind (die volle Datei hat 17 MB pro Tag).
Lädt man einen Betriebstag erneut, wird seine Datei ersetzt.
"""
import csv
import io
import sys
import urllib.request
from collections import Counter
from pathlib import Path

URL = "https://data.sbb.ch/api/explore/v2.1/catalog/datasets/ist-daten-sbb/exports/csv?delimiter=%3B&limit=-1"
OUT = Path(__file__).with_name("daten")
COLUMNS = ["betriebstag", "fahrt_bezeichner", "linien_text", "verkehrsmittel_text", "faellt_aus_tf", "durchfahrt_tf",
           "bpuic", "haltestellen_name", "ankunftszeit", "an_prognose", "an_prognose_status",
           "abfahrtszeit", "ab_prognose", "ab_prognose_status"]


def main() -> int:
    OUT.mkdir(exist_ok=True)
    print("Lade", URL, flush=True)
    with urllib.request.urlopen(URL, timeout=600) as r:
        text = r.read().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text), delimiter=";"))
    if not rows:
        print("FEHLER: Datensatz ist leer")
        return 1
    days = Counter(r["betriebstag"] for r in rows)
    for day, n in sorted(days.items()):
        path = OUT / f"ist_daten_{day.replace('-', '')}.csv"
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(COLUMNS)
            w.writerows([r[c] for c in COLUMNS] for r in rows if r["betriebstag"] == day)
        print(f"Datei gespeichert: {path} ({n} Zeilen, {path.stat().st_size // 1024} KB)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
