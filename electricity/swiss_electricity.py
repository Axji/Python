"""Lädt die monatliche Schweizerische Elektrizitätsbilanz des BFE und speichert sie als CSV-Datei und in einer SQLite-Datenbank.

Quelle: Bundesamt für Energie (BFE), Schweizerische Elektrizitätsstatistik, Datensatz "Elektrizitätsbilanz der Schweiz -
Monatswerte" (ogd35) auf opendata.swiss. Die Datei enthält alle Monate seit Januar 2000 in GWh: Erzeugung nach Kraftwerksart
(Laufwerke, Speicherwerke, Kernkraft, Thermische, Wind, Photovoltaik), Pumpstrom, Einfuhr, Ausfuhr, Landesverbrauch, Verluste
und Endverbrauch. Die jüngsten Monate sind provisorisch (Spalte "Definitiv" = 0) und werden bei späteren Abrufen korrigiert.

Das Ergebnis landet an zwei Orten im Ordner daten/ neben diesem Skript:
- elektrizitaetsbilanz_monatswerte_JJJJMMTT.csv: die unveränderte Datei vom Abruftag (so lassen sich Korrekturen später vergleichen)
- electricity.db: Tabelle monthly (ein Datensatz pro Monat, wird bei jedem Abruf aktualisiert), Tabelle abrufe (Protokoll)
  und Auswertungs-Sichten (Views) für den Vergleich über die Zeit:
    v_monat        Monat mit Wasserkraft gesamt, Überschuss (Erzeugung minus Verbrauch), Über-/Unterproduktion, Eigendeckung, Anteile
    v_jahr         Jahressummen (vollstaendig = 1 nur bei zwölf Monaten) mit Vergleich zum Vorjahr
    v_halbjahr     Winter (Oktober bis März) und Sommer (April bis September) je Jahr
    v_vorjahr      jeder Monat neben demselben Monat des Vorjahrs, mit Differenz und Prozent

Über- und Unterproduktion: Überschuss = Nettoerzeugung (nach Abzug des Pumpstroms) minus Landesverbrauch. Das ist genau
Ausfuhr minus Einfuhr. Positiv heisst, die Schweiz hat mehr erzeugt als verbraucht (Ausfuhrüberschuss), negativ heisst, sie hat
Strom netto importiert.

Aufruf:
    py electricity/swiss_electricity.py              laden, speichern und eine Zusammenfassung ausgeben
    py electricity/swiss_electricity.py --offline    nur die zuletzt gespeicherte CSV-Datei neu in die Datenbank einlesen
    py electricity/swiss_electricity.py --daten ORDNER   anderer Ordner für CSV-Dateien und Datenbank
"""
import argparse
import csv
import datetime
import glob
import io
import os
import sqlite3
import ssl
import sys
import time
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'daten')
CSV_PREFIX = 'elektrizitaetsbilanz_monatswerte_'
DB_NAME = 'electricity.db'
SOURCE_URL = 'https://www.bfe-ogd.ch/ogd35/ogd35_schweizerische_elektrizitaetsbilanz_monatswerte.csv'
REQUEST_TIMEOUT = 30  # Sekunden
REQUEST_ATTEMPTS = 3  # so oft wird die Adresse versucht, bevor der Abruf scheitert
TOLERANCE_GWH = 3  # erlaubte Rundungsabweichung bei den Kontrollsummen

# Spalten der Quelldatei und die zugehörigen Spalten der Tabelle (alles GWh)
VALUE_COLUMNS = [
    ('Erzeugung_Laufwerk_GWh', 'laufwerk_gwh'),
    ('Erzeugung_Speicherwerk_GWh', 'speicherwerk_gwh'),
    ('Erzeugung_Kernkraftwerk_GWh', 'kernkraft_gwh'),
    ('Erzeugung_andere_GWh', 'andere_gwh'),
    ('Erzeugung_Thermische_GWh', 'thermisch_gwh'),
    ('Erzeugung_Windkraft_GWh', 'wind_gwh'),
    ('Erzeugung_Photovoltaik_GWh', 'photovoltaik_gwh'),
    ('Landeserzeugung_GWh', 'landeserzeugung_gwh'),
    ('Verbrauch_Speicherpumpen_GWh', 'speicherpumpen_gwh'),
    ('Erzeugung_netto_GWh', 'erzeugung_netto_gwh'),
    ('Einfuhr_GWh', 'einfuhr_gwh'),
    ('Ausfuhr_GWh', 'ausfuhr_gwh'),
    ('Landesverbrauch_GWh', 'landesverbrauch_gwh'),
    ('Verluste_GWh', 'verluste_gwh'),
    ('Endverbrauch_GWh', 'endverbrauch_gwh'),
]
DB_VALUE_NAMES = [db for _, db in VALUE_COLUMNS]
GENERATION_PARTS = ['laufwerk_gwh', 'speicherwerk_gwh', 'kernkraft_gwh', 'andere_gwh', 'thermisch_gwh', 'wind_gwh', 'photovoltaik_gwh']
REQUIRED_COLUMNS = ['Jahr', 'Monat', 'Definitiv'] + [csv_name for csv_name, _ in VALUE_COLUMNS]


def make_ssl_context():
    """TLS-Einstellungen für den Download.

    Python 3.14 (OpenSSL 3.5) schickt beim Verbindungsaufbau standardmässig einen grossen Post-Quantum-Schlüssel mit, den manche
    Server mit "SSL: UNEXPECTED_EOF_WHILE_READING" abbrechen. Mit der klassischen Kurve X25519 klappt es zuverlässig.
    Kennt die Python-Version die Kurve nicht, gilt die Standardeinstellung.
    """
    context = ssl.create_default_context()
    try:
        context.set_ecdh_curve('X25519')
    except ValueError:
        pass
    return context


SSL_CONTEXT = make_ssl_context()


def fetch_csv(url=SOURCE_URL):
    """Lädt die CSV-Datei herunter und gibt sie als Text zurück. Bei einem Verbindungsfehler wird bis zu REQUEST_ATTEMPTS-mal versucht."""
    req = urllib.request.Request(url)
    # Eigener User-Agent, damit der Server den Zugriff zuordnen kann
    req.add_header('User-Agent', 'electricity-downloader/1.0 (Contact: axel.zenklusen@gmail.com)')
    for attempt in range(1, REQUEST_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CONTEXT) as response:
                data = response.read()
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == REQUEST_ATTEMPTS:
                raise
            time.sleep(2 * attempt)
    return data.decode('utf-8-sig')


def to_number(text):
    """Wandelt einen CSV-Wert in eine Zahl um. "NULL" und leere Felder (Kraftwerksart in dem Jahr nicht ausgewiesen) werden zu None."""
    text = text.strip()
    if text == '' or text.upper() == 'NULL':
        return None
    return float(text)


def parse_csv(text):
    """Liest die CSV-Datei in eine Liste von Dictionaries (ein Eintrag pro Monat, Schlüssel wie die Tabellenspalten).

    Fehlt eine erwartete Spalte, bricht die Funktion mit ValueError ab, bevor irgendetwas überschrieben wird.
    """
    reader = csv.DictReader(io.StringIO(text))
    missing = [name for name in REQUIRED_COLUMNS if name not in (reader.fieldnames or [])]
    if missing:
        raise ValueError('In der CSV-Datei fehlen Spalten: ' + ', '.join(missing))
    rows = []
    for line in reader:
        row = {'jahr': int(line['Jahr']), 'monat': int(line['Monat']), 'definitiv': int(line['Definitiv'])}
        for csv_name, db_name in VALUE_COLUMNS:
            row[db_name] = to_number(line[csv_name])
        rows.append(row)
    if not rows:
        raise ValueError('Die CSV-Datei enthält keine Daten')
    return rows


def check_balance(row):
    """Prüft die Rechenregeln der Bilanz und gibt eine Liste von Abweichungen zurück (leer, wenn alles stimmt).

    Landeserzeugung = Summe der Kraftwerksarten; Nettoerzeugung = Landeserzeugung - Pumpstrom;
    Landesverbrauch = Nettoerzeugung + Einfuhr - Ausfuhr; Endverbrauch = Landesverbrauch - Verluste.
    """
    problems = []

    def check(name, actual, *terms):
        # terms: (Vorzeichen, Wert); fehlt ein Wert, kann die Regel nicht geprüft werden
        if actual is None or any(value is None for _, value in terms):
            return
        expected = sum(sign * value for sign, value in terms)
        if abs(actual - expected) > TOLERANCE_GWH:
            problems.append(f'{name}: {actual:.0f} statt {expected:.0f}')

    parts = [(1, row[name] or 0) for name in GENERATION_PARTS]
    check('Landeserzeugung', row['landeserzeugung_gwh'], *parts)
    check('Nettoerzeugung', row['erzeugung_netto_gwh'], (1, row['landeserzeugung_gwh']), (-1, row['speicherpumpen_gwh']))
    check('Landesverbrauch', row['landesverbrauch_gwh'], (1, row['erzeugung_netto_gwh']), (1, row['einfuhr_gwh']), (-1, row['ausfuhr_gwh']))
    check('Endverbrauch', row['endverbrauch_gwh'], (1, row['landesverbrauch_gwh']), (-1, row['verluste_gwh']))
    return problems


def csv_files(data_dir):
    """Alle gespeicherten CSV-Dateien, die älteste zuerst (das Datum steht im Namen)."""
    return sorted(glob.glob(os.path.join(data_dir, CSV_PREFIX + '*.csv')))


def save_csv(text, data_dir, today=None):
    """Speichert die heruntergeladene Datei unverändert mit dem Abrufdatum im Namen und gibt den Pfad zurück.

    Ein zweiter Abruf am selben Tag überschreibt die Datei des Tages.
    """
    today = today or datetime.date.today()
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, f'{CSV_PREFIX}{today:%Y%m%d}.csv')
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    os.replace(tmp_path, path)  # erst vollständig schreiben, dann ersetzen
    return path


# ---------------------------------------------------------------- Datenbank


def init_db(conn):
    """Legt die Tabellen an, falls sie noch fehlen."""
    value_defs = ',\n        '.join(f'{name} REAL' for name in DB_VALUE_NAMES)
    conn.executescript(f"""
    CREATE TABLE IF NOT EXISTS monthly (
        jahr INTEGER NOT NULL,
        monat INTEGER NOT NULL,
        periode TEXT NOT NULL,          -- 'JJJJ-MM', sortiert chronologisch
        definitiv INTEGER NOT NULL,     -- 1 = definitiver Wert, 0 = provisorisch
        {value_defs},
        abgerufen_am TEXT NOT NULL,     -- Zeitpunkt, an dem dieser Datensatz zuletzt geschrieben wurde
        PRIMARY KEY (jahr, monat)
    );
    CREATE TABLE IF NOT EXISTS abrufe (
        abruf_am TEXT NOT NULL,
        quelle TEXT NOT NULL,
        zeilen INTEGER NOT NULL,
        neueste_periode TEXT NOT NULL,
        neue_zeilen INTEGER NOT NULL,
        geaenderte_zeilen INTEGER NOT NULL
    );
    """)


def save_to_db(conn, rows, retrieved_at):
    """Schreibt die Monatsdaten in die Tabelle monthly und gibt (neue Zeilen, geänderte Zeilen) zurück.

    Ein bestehender Monat wird überschrieben (provisorische Werte werden später korrigiert). "geändert" zählt nur Monate,
    deren Werte sich tatsächlich unterscheiden.
    """
    value_names = ['definitiv'] + DB_VALUE_NAMES
    select_sql = f'SELECT {", ".join(value_names)} FROM monthly WHERE jahr = ? AND monat = ?'
    columns = ['jahr', 'monat', 'periode'] + value_names + ['abgerufen_am']
    updates = ', '.join(f'{name} = excluded.{name}' for name in columns[2:])
    upsert_sql = (f'INSERT INTO monthly ({", ".join(columns)}) VALUES ({", ".join("?" * len(columns))}) '
                  f'ON CONFLICT (jahr, monat) DO UPDATE SET {updates}')
    new_rows = changed_rows = 0
    for row in rows:
        values = tuple(row[name] for name in value_names)
        old = conn.execute(select_sql, (row['jahr'], row['monat'])).fetchone()
        if old is None:
            new_rows += 1
        elif old != values:
            changed_rows += 1
        periode = f'{row["jahr"]:04d}-{row["monat"]:02d}'
        conn.execute(upsert_sql, (row['jahr'], row['monat'], periode, *values, retrieved_at))
    return new_rows, changed_rows


def log_retrieval(conn, retrieved_at, source, rows, new_rows, changed_rows):
    """Trägt den Abruf in die Tabelle abrufe ein."""
    newest = max((r['jahr'], r['monat']) for r in rows)
    conn.execute('INSERT INTO abrufe VALUES (?, ?, ?, ?, ?, ?)',
                 (retrieved_at, source, len(rows), f'{newest[0]:04d}-{newest[1]:02d}', new_rows, changed_rows))


# Summen und Kennzahlen, die für Jahr und Halbjahr gleich berechnet werden
GROUP_COLUMNS = """
    COUNT(*) AS monate,
    MIN(definitiv) AS definitiv,
    SUM(wasserkraft_gwh) AS wasserkraft_gwh,
    SUM(kernkraft_gwh) AS kernkraft_gwh,
    SUM(thermisch_gwh) AS thermisch_gwh,
    SUM(wind_gwh) AS wind_gwh,
    SUM(photovoltaik_gwh) AS photovoltaik_gwh,
    SUM(landeserzeugung_gwh) AS landeserzeugung_gwh,
    SUM(speicherpumpen_gwh) AS speicherpumpen_gwh,
    SUM(erzeugung_netto_gwh) AS erzeugung_netto_gwh,
    SUM(einfuhr_gwh) AS einfuhr_gwh,
    SUM(ausfuhr_gwh) AS ausfuhr_gwh,
    SUM(landesverbrauch_gwh) AS landesverbrauch_gwh,
    SUM(verluste_gwh) AS verluste_gwh,
    SUM(endverbrauch_gwh) AS endverbrauch_gwh,
    SUM(ueberschuss_gwh) AS ueberschuss_gwh,
    ROUND(100.0 * SUM(erzeugung_netto_gwh) / SUM(landesverbrauch_gwh), 1) AS eigendeckung_pct,
    CASE WHEN SUM(ueberschuss_gwh) > 0 THEN 'Ueberproduktion'
         WHEN SUM(ueberschuss_gwh) < 0 THEN 'Unterproduktion' ELSE 'ausgeglichen' END AS status"""

# Spalten, die v_vorjahr mit dem Vorjahresmonat vergleicht
COMPARE_COLUMNS = ['landeserzeugung_gwh', 'wasserkraft_gwh', 'kernkraft_gwh', 'photovoltaik_gwh', 'einfuhr_gwh', 'ausfuhr_gwh',
                   'landesverbrauch_gwh', 'ueberschuss_gwh']


def create_views(conn):
    """Erstellt die Auswertungs-Sichten neu (sie werden bei jedem Lauf ersetzt, damit Änderungen hier wirksam werden)."""
    for view in ('v_vorjahr', 'v_halbjahr', 'v_jahr', 'v_monat'):
        conn.execute(f'DROP VIEW IF EXISTS {view}')
    conn.execute("""
    CREATE VIEW v_monat AS
    SELECT periode, jahr, monat, definitiv,
        laufwerk_gwh + speicherwerk_gwh AS wasserkraft_gwh,
        laufwerk_gwh, speicherwerk_gwh, kernkraft_gwh, andere_gwh, thermisch_gwh, wind_gwh, photovoltaik_gwh,
        landeserzeugung_gwh, speicherpumpen_gwh, erzeugung_netto_gwh, einfuhr_gwh, ausfuhr_gwh,
        landesverbrauch_gwh, verluste_gwh, endverbrauch_gwh,
        erzeugung_netto_gwh - landesverbrauch_gwh AS ueberschuss_gwh,
        CASE WHEN erzeugung_netto_gwh > landesverbrauch_gwh THEN 'Ueberproduktion'
             WHEN erzeugung_netto_gwh < landesverbrauch_gwh THEN 'Unterproduktion' ELSE 'ausgeglichen' END AS status,
        ROUND(100.0 * erzeugung_netto_gwh / landesverbrauch_gwh, 1) AS eigendeckung_pct,
        ROUND(100.0 * (laufwerk_gwh + speicherwerk_gwh) / landeserzeugung_gwh, 1) AS anteil_wasserkraft_pct,
        ROUND(100.0 * kernkraft_gwh / landeserzeugung_gwh, 1) AS anteil_kernkraft_pct,
        ROUND(100.0 * photovoltaik_gwh / landeserzeugung_gwh, 1) AS anteil_photovoltaik_pct
    FROM monthly""")
    conn.execute(f"""
    CREATE VIEW v_jahr AS
    WITH j AS (
        SELECT jahr, {GROUP_COLUMNS}, COUNT(*) = 12 AS vollstaendig
        FROM v_monat GROUP BY jahr)
    SELECT *,
        landeserzeugung_gwh - LAG(landeserzeugung_gwh) OVER (ORDER BY jahr) AS erzeugung_diff_vorjahr_gwh,
        landesverbrauch_gwh - LAG(landesverbrauch_gwh) OVER (ORDER BY jahr) AS verbrauch_diff_vorjahr_gwh,
        ueberschuss_gwh - LAG(ueberschuss_gwh) OVER (ORDER BY jahr) AS ueberschuss_diff_vorjahr_gwh
    FROM j ORDER BY jahr""")
    conn.execute(f"""
    CREATE VIEW v_halbjahr AS
    WITH k AS (
        SELECT *,
            CASE WHEN monat >= 10 OR monat <= 3 THEN 'Winter' ELSE 'Sommer' END AS typ,
            CASE WHEN monat <= 3 THEN jahr - 1 ELSE jahr END AS start_jahr
        FROM v_monat)
    SELECT typ || ' ' || start_jahr || CASE WHEN typ = 'Winter' THEN '/' || SUBSTR(CAST(start_jahr + 1 AS TEXT), 3) ELSE '' END AS halbjahr,
        typ, start_jahr, COUNT(*) = 6 AS vollstaendig, {GROUP_COLUMNS}
    FROM k GROUP BY typ, start_jahr
    ORDER BY start_jahr, typ""")
    compare = ',\n        '.join(
        f'm.{c} AS {c}, v.{c} AS {c[:-4]}_vorjahr_gwh, m.{c} - v.{c} AS {c[:-4]}_diff_gwh, '
        f'ROUND(100.0 * (m.{c} - v.{c}) / NULLIF(v.{c}, 0), 1) AS {c[:-4]}_diff_pct' for c in COMPARE_COLUMNS)
    conn.execute(f"""
    CREATE VIEW v_vorjahr AS
    SELECT m.periode, m.definitiv,
        {compare}
    FROM v_monat m LEFT JOIN v_monat v ON v.jahr = m.jahr - 1 AND v.monat = m.monat
    ORDER BY m.periode""")


# ---------------------------------------------------------------- Ausgabe


def fmt(value, decimals=0):
    """Zahl mit Hochkomma als Tausendertrenner (Schweizer Schreibweise); None als Strich."""
    if value is None:
        return '-'
    return f'{value:,.{decimals}f}'.replace(',', "'")


def print_summary(conn, months=12):
    """Gibt den neuesten Monat mit allen Kraftwerksarten sowie die letzten Monate im Überblick aus."""
    conn.row_factory = sqlite3.Row
    try:
        latest = conn.execute('SELECT * FROM v_monat ORDER BY periode DESC LIMIT 1').fetchone()
        if latest is None:
            print('Keine Daten in der Datenbank.')
            return
        year_ago = conn.execute('SELECT * FROM v_vorjahr WHERE periode = ?', (latest['periode'],)).fetchone()
        recent = conn.execute('SELECT * FROM v_monat ORDER BY periode DESC LIMIT ?', (months,)).fetchall()
    finally:
        conn.row_factory = None
    state = 'definitiv' if latest['definitiv'] else 'provisorisch'
    print(f'\nNeuester Monat: {latest["periode"]} ({state}), alle Werte in GWh')
    generation = [('Wasserkraft (Laufwerke + Speicher)', 'wasserkraft_gwh'), ('  davon Laufwerke', 'laufwerk_gwh'),
                  ('  davon Speicherwerke', 'speicherwerk_gwh'), ('Kernkraft', 'kernkraft_gwh'), ('Photovoltaik', 'photovoltaik_gwh'),
                  ('Wind', 'wind_gwh'), ('Thermische', 'thermisch_gwh'), ('Andere (bis 2019)', 'andere_gwh')]
    for label, name in generation:
        if latest[name] is None:
            continue
        share = 100 * latest[name] / latest['landeserzeugung_gwh']
        print(f'  {label:<36}{fmt(latest[name]):>8}  {share:5.1f} %')
    print(f'  {"Landeserzeugung":<36}{fmt(latest["landeserzeugung_gwh"]):>8}')
    print(f'  {"Pumpstrom (Speicherpumpen)":<36}{fmt(latest["speicherpumpen_gwh"]):>8}')
    print(f'  {"Nettoerzeugung":<36}{fmt(latest["erzeugung_netto_gwh"]):>8}')
    print(f'  {"Einfuhr":<36}{fmt(latest["einfuhr_gwh"]):>8}')
    print(f'  {"Ausfuhr":<36}{fmt(latest["ausfuhr_gwh"]):>8}')
    print(f'  {"Landesverbrauch":<36}{fmt(latest["landesverbrauch_gwh"]):>8}')
    print(f'  => {latest["status"]}: Erzeugung minus Verbrauch = {fmt(latest["ueberschuss_gwh"])} GWh, '
          f'Eigendeckung {latest["eigendeckung_pct"]} %')
    if year_ago and year_ago['landeserzeugung_vorjahr_gwh'] is not None:
        print(f'  Vorjahresmonat: Landeserzeugung {fmt(year_ago["landeserzeugung_vorjahr_gwh"])} '
              f'({fmt(year_ago["landeserzeugung_diff_gwh"])} GWh, {year_ago["landeserzeugung_diff_pct"]} %)')
    print(f'\nLetzte {len(recent)} Monate:')
    print(f'  {"Monat":<9}{"Erzeugung":>10}{"Verbrauch":>10}{"Einfuhr":>9}{"Ausfuhr":>9}{"Ueberschuss":>13}  {"Status":<16}{"Eigendeckung":>12}')
    for r in reversed(recent):
        print(f'  {r["periode"]:<9}{fmt(r["erzeugung_netto_gwh"]):>10}{fmt(r["landesverbrauch_gwh"]):>10}{fmt(r["einfuhr_gwh"]):>9}'
              f'{fmt(r["ausfuhr_gwh"]):>9}{fmt(r["ueberschuss_gwh"]):>13}  {r["status"]:<16}{r["eigendeckung_pct"]:>11} %')


# ---------------------------------------------------------------- Ablauf


def run(data_dir=DATA_DIR, offline=False, fetch=None):
    """Lädt (oder liest) die Daten, speichert CSV und Datenbank und gibt die Zusammenfassung aus."""
    os.makedirs(data_dir, exist_ok=True)
    if offline:
        files = csv_files(data_dir)
        if not files:
            raise FileNotFoundError(f'Keine gespeicherte CSV-Datei in {data_dir}. Erst ohne --offline ausführen.')
        csv_path = files[-1]
        with open(csv_path, encoding='utf-8-sig', newline='') as f:
            text = f.read()
        print(f'Lese {os.path.basename(csv_path)} (ohne Download)')
    else:
        print(f'Lade {SOURCE_URL}')
        text = (fetch or fetch_csv)()  # fetch_csv erst hier nachschlagen, damit Tests es ersetzen können
    rows = parse_csv(text)  # prüft die Spalten, bevor etwas gespeichert wird
    if not offline:
        csv_path = save_csv(text, data_dir)
        print(f'CSV gespeichert: {csv_path}')
    problems = [(r['jahr'], r['monat'], p) for r in rows for p in check_balance(r)]
    if problems:
        print(f'Achtung: {len(problems)} Abweichung(en) in den Rechenregeln der Quelle:')
        for year, month, problem in problems[:10]:
            print(f'  {year}-{month:02d} {problem}')

    retrieved_at = datetime.datetime.now().isoformat(timespec='seconds')
    db_path = os.path.join(data_dir, DB_NAME)
    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)
        new_rows, changed_rows = save_to_db(conn, rows, retrieved_at)
        log_retrieval(conn, retrieved_at, os.path.basename(csv_path) if offline else SOURCE_URL, rows, new_rows, changed_rows)
        create_views(conn)
        conn.commit()
        print(f'Datenbank {db_path}: {len(rows)} Monate, {new_rows} neu, {changed_rows} geändert')
        print_summary(conn)
    finally:
        conn.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Lädt die monatliche Schweizerische Elektrizitätsbilanz (BFE) in CSV und SQLite.')
    parser.add_argument('--offline', action='store_true', help='nicht herunterladen, sondern die zuletzt gespeicherte CSV-Datei einlesen')
    parser.add_argument('--daten', default=DATA_DIR, help='Ordner für CSV-Dateien und Datenbank (Standard: daten/ neben dem Skript)')
    args = parser.parse_args(argv)
    try:
        run(args.daten, args.offline)
    except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, FileNotFoundError) as error:
        print(f'Fehler: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
