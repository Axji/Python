"""Lädt die Ist-Daten der Züge von opentransportdata.swiss (Datensatz ist-daten-v2) und speichert sie als CSV-Datei pro
Betriebstag in daten/ist_daten_JJJJMMTT.csv.

Die Plattform bietet die letzten rund 50 Betriebstage als Tagesdateien an (je etwa 500 MB, alle Verkehrsmittel der Schweiz).
Fehlt ein Tag in daten/, weil der PC aus war, wird er darum einfach nachgeladen. Standardmässig werden die letzten 14 Tage
geprüft; vorhandene Tage werden übersprungen.

Gespeichert werden nur Züge aller Bahnunternehmen (PRODUKT_ID = Zug, also ohne Bus, Tram, Metro und Schiff; SBB, BLS, Thurbo,
RhB, ...) und nur die Spalten, die für die Pünktlichkeitsauswertung nötig sind (etwa 25 MB pro Tag). Datum und Zeiten werden ins ISO-Format gebracht (JJJJ-MM-TT, JJJJ-MM-TTThh:mm:ss).

Aufruf: get_sbb_data.py [--tage N] [--neu]   (--neu lädt auch bereits vorhandene Tage erneut und ersetzt ihre Dateien)
"""
import argparse
import csv
import datetime as dt
import io
import re
import sys
import time
import urllib.request
from pathlib import Path

PAGE = "https://data.opentransportdata.swiss/en/dataset/ist-daten-v2"
OUT = Path(__file__).with_name("daten")
UA = {"User-Agent": "Mozilla/5.0 (sbb-puenktlichkeit)"}
COLUMNS = ["betriebstag", "fahrt_bezeichner", "linien_text", "verkehrsmittel_text", "faellt_aus_tf", "durchfahrt_tf",
           "bpuic", "haltestellen_name", "ankunftszeit", "an_prognose", "an_prognose_status",
           "abfahrtszeit", "ab_prognose", "ab_prognose_status"]
TIME_COLUMNS = {"ankunftszeit", "an_prognose", "abfahrtszeit", "ab_prognose"}
LINK = re.compile(r'https://[^"\s]*/download/(\d{4}-\d{2}-\d{2})_istdaten\.csv', re.I)


def open_url(url: str, timeout: int, tries: int = 4):
    """Öffnet eine URL mit Wiederholungen (wachsende Pause)."""
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
        except OSError as e:
            if i == tries - 1:
                raise
            print(f"   Abruf fehlgeschlagen ({e}), neuer Versuch in {10 * (i + 1)} s", flush=True)
            time.sleep(10 * (i + 1))


def available_days() -> dict[str, str]:
    """Betriebstag (JJJJ-MM-TT) -> Download-Adresse, aus der Dateiliste des Datensatzes."""
    with open_url(PAGE, 120) as r:
        html = r.read().decode("utf-8", "replace")
    return {m.group(1): m.group(0) for m in LINK.finditer(html)}


def iso_time(value: str) -> str:
    """'27.10.2026 22:34' oder '27.10.2026 22:35:00' -> '2026-10-27T22:34:00'. Leer bleibt leer."""
    if not value:
        return ""
    date, _, clock = value.partition(" ")
    d, m, y = date.split(".")
    return f"{y}-{m}-{d}T{clock if clock.count(':') == 2 else clock + ':00'}"


def convert(row: dict[str, str]) -> list[str]:
    out = []
    for c in COLUMNS:
        v = row[c.upper()]
        if c == "betriebstag":
            d, m, y = v.split(".")
            v = f"{y}-{m}-{d}"
        elif c in TIME_COLUMNS:
            v = iso_time(v)
        elif c in ("faellt_aus_tf", "durchfahrt_tf"):
            v = v.capitalize()  # true -> True wie im früheren Datensatz
        out.append(v)
    return out


def download_day(day: str, url: str) -> int:
    """Lädt einen Tag im Datenstrom, filtert auf Züge und schreibt ist_daten_JJJJMMTT.csv. Gibt die Zeilenzahl zurück."""
    path = OUT / f"ist_daten_{day.replace('-', '')}.csv"
    tmp = path.with_suffix(".tmp")
    n = 0
    t0 = time.time()
    with open_url(url, 600) as r, open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(COLUMNS)
        text = io.TextIOWrapper(r, encoding="utf-8-sig", newline="")
        for row in csv.DictReader(text, delimiter=";"):
            if row["PRODUKT_ID"] == "Zug":
                w.writerow(convert(row))
                n += 1
    if n == 0:
        tmp.unlink()
        raise OSError(f"{day}: keine Zug-Zeilen gefunden")
    tmp.replace(path)  # erst ersetzen, wenn die Datei komplett ist
    print(f"Datei gespeichert: {path} ({n} Zeilen, {path.stat().st_size // 1024} KB, {time.time() - t0:.0f} s)", flush=True)
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tage", type=int, default=14, help="so viele der letzten Betriebstage prüfen (Standard 14, es gibt rund 50)")
    ap.add_argument("--neu", action="store_true", help="auch vorhandene Tage erneut laden")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    print("Lese Dateiliste", PAGE, flush=True)
    days = available_days()
    if not days:
        print("FEHLER: keine Tagesdateien in der Dateiliste gefunden")
        return 1
    wanted = sorted(days)[-args.tage:]
    todo = [d for d in wanted if args.neu or not (OUT / f"ist_daten_{d.replace('-', '')}.csv").exists()]
    print(f"Verfügbar: {min(days)} bis {max(days)}; geprüft: {wanted[0]} bis {wanted[-1]}; zu laden: {len(todo)}", flush=True)
    errors = 0
    for d in todo:
        try:
            download_day(d, days[d])
        except OSError as e:
            errors += 1
            print(f"FEHLER bei {d}: {e}", flush=True)
    if errors:
        return 1
    print("Alles aktuell" if not todo else f"{len(todo)} Tag(e) geladen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
