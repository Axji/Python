# Python-Projekte – Dokumentation

Sammlung kleiner Python-Projekte von Axel Zenklusen: Datenerfassung (Fitnesspark-Auslastung, Wetterdaten), ein
Autorennen mit lernender KI, einige Spiele und Übungen. Dieses Dokument beschreibt Aufbau, Einrichtung und Bedienung.
Warum etwas so gelöst ist, steht in [ENTSCHEIDUNGEN.md](ENTSCHEIDUNGEN.md).

## Inhalt

1. [Einrichtung](#1-einrichtung)
2. [Überblick über die Projekte](#2-überblick-über-die-projekte)
3. [Fitnesspark-Auslastung](#3-fitnesspark-auslastung)
4. [CarRace (Autorennen mit KI)](#4-carrace-autorennen-mit-ki)
5. [Wetterdaten (Weather)](#5-wetterdaten-weather)
6. [Stromstatistik (electricity)](#6-stromstatistik-electricity)
7. [Weitere Skripte](#7-weitere-skripte)
8. [Konfiguration und Geheimnisse](#8-konfiguration-und-geheimnisse)
9. [Arbeitsweise mit Git](#9-arbeitsweise-mit-git)
10. [Bekannte Einschränkungen](#10-bekannte-einschränkungen)

---

## 1. Einrichtung

**Voraussetzungen:** Windows, Python 3.13 (getestet mit 3.13.15), Git. Als Editor ist VS Code vorbereitet.

```bash
git clone https://github.com/Axji/Python.git C:\dev\Phyton
cd C:\dev\Phyton
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Alle Skripte werden mit dem Python aus der `venv` gestartet, zum Beispiel:

```bash
.\venv\Scripts\python.exe Bingo.py
```

**Pakete** (`requirements.txt`): `requests`, `numpy`, `pillow`, `pygame-ce`, `pymssql`. Alles andere (SQLite, CSV, Tkinter)
gehört zur Standardbibliothek von Python.

**pygame-ce statt pygame:** Das Projekt nutzt `pygame-ce` (der gepflegte Fork). Im Code bleibt `import pygame` unverändert. `pygame` und
`pygame-ce` dürfen nicht gleichzeitig installiert sein. Beim Umstellen einer bestehenden `venv` erst `pip uninstall pygame` und dann
`pip install -r requirements.txt` ausführen.

**VS Code:** Der Ordner `.vscode/` enthält die Einstellungen. Der Interpreter zeigt auf `venv`, Ruff formatiert beim
Speichern und sortiert die Imports. Mit **F5** wird die geöffnete Datei im Debugger gestartet. Empfohlene
Erweiterungen: Python, Pylance, Ruff, Jupyter.

**Prüfen:** Die Ruff-Regeln stehen in `pyproject.toml`. Lint und Tests laufen so (auch in GitHub Actions, `.github/workflows/ci.yml`):

```bash
.envScriptspython.exe -m pip install ruff pytest
.envScripts
uff.exe check .
.envScriptspython.exe -m pytest
```

> Die `venv` gehört nicht ins Repository (steht in `.gitignore`). Nach einem frischen Klon wird sie mit den Befehlen oben
> neu aufgebaut.

---

## 2. Überblick über die Projekte

| Ordner / Datei | Zweck | Zusatzpakete |
|---|---|---|
| `Fitnesspark_belegung.py` | Auslastung der Fitnessparks abrufen und speichern | requests |
| `fitnesspark_db.py` | Gemeinsamer SQLite-Zugriff der Fitnesspark-Skripte | – |
| `fitnessparks/` | Import, Bereinigung und Auswertung der Fitnesspark-Daten | – |
| `CarRace/` | Autorennen mit regelbasierter und lernender KI | pygame-ce |
| `Weather/` | Klimadaten von MeteoSchweiz laden, SQLite-Ablage | – |
| `electricity/` | Monatliche Schweizer Strombilanz (BFE) laden, CSV und SQLite, Vergleich über die Zeit | – |
| `mandelbaum.py` | Mandelbrot-Generator mit Fenster | numpy, pillow |
| `matrix_simulation.py` | 10×10-Matrix, jede Zelle zählt in einem eigenen Thread | – |
| `game_of_life.py` | Conways Game of Life mit Fenster: Zeichnen mit der Maus, Start/Stop, Einzelschritt | pygame-ce |
| `Bingo.py`, `JumpAndRun1.py` | Kleine Spiele | pygame-ce (JumpAndRun) |
| `jumprun1/` | Jump-and-Run mit Pixeloptik, Schiessen und Plan (siehe `jumprun1/README.md`) | pygame-ce |
| `sort.py`, `run.py`, `global_lib.py` | Sortieralgorithmen mit Zählern und Demo | – |

---

## 3. Fitnesspark-Auslastung

Eine Pipeline in vier Schritten. Alle Daten liegen im Ordner `data/` (wird automatisch angelegt und ist **nicht** im
Repository).

```
Fitnesspark_belegung.py  ->  data/Fitnesspark_Belegung_JJJJ-MM-TT.csv   (Sicherung, eine Datei pro Tag)
                         ->  data/fitnessparks.db  (Tabelle besucher)
fitnesspark_csv_to_sqlite.py   ältere CSV-Dateien nachträglich in die Datenbank laden
fitnesspark_clean.py           gleiche Folgewerte in der Datenbank entfernen
fitnesspark_report.py          interaktive HTML-Auswertung aus den CSV-Dateien
```

### 3.1 Daten erfassen – `Fitnesspark_belegung.py`

Ruft für 17 Standorte die aktuelle Besucherzahl von der Website des Fitnessparks ab (Zeitlimit 15 Sekunden je Abruf) und
schreibt sie in die Tagesdatei und in die Datenbank. Ein Fehler bei einem Standort stoppt die anderen nicht. Das Skript
ist für den regelmässigen Aufruf gedacht, zum Beispiel alle 5 Minuten über die Windows-Aufgabenplanung.

```bash
.\venv\Scripts\python.exe Fitnesspark_belegung.py
```

Es werden nur Zeilen mit einem Wert **grösser als 0** gespeichert. Ein geschlossener oder leerer Park fehlt also in den
Daten (siehe 3.4).

### 3.2 Datenbank – `fitnesspark_db.py`

Tabelle `besucher` mit den Spalten `fitnesspark`, `belegung`, `Timestamp` und `loaduser`. Die Kombination aus
`fitnesspark` und `Timestamp` ist eindeutig, mehrfaches Einfügen derselben Messung erzeugt keine doppelten Zeilen.
Ordner, Datei und Tabelle werden bei Bedarf angelegt. Es braucht keinen Datenbankserver und kein Passwort.

### 3.3 Nachladen und Bereinigen

```bash
.\venv\Scripts\python.exe fitnessparks\fitnesspark_csv_to_sqlite.py     # alle CSV in data/ laden
.\venv\Scripts\python.exe fitnessparks\fitnesspark_clean.py --dry-run   # Testlauf: nur anzeigen
.\venv\Scripts\python.exe fitnessparks\fitnesspark_clean.py             # wirklich löschen
.\venv\Scripts\python.exe fitnessparks\fitnesspark_csv_to_sqlite.py --since 2026-11-02   # nur CSV ab diesem Tag laden
.\venv\Scripts\python.exe fitnessparks\fitnesspark_clean.py --since 2026-11-02           # nur ab diesem Tag bereinigen
```

- **Nur ein Teil (`--since JJJJ-MM-TT`):** Import und Bereinigung lassen sich auf die neuesten Tage beschränken. Das
  Ergebnis ist dasselbe wie bei einem vollständigen Lauf, wenn der Rest der Datenbank schon bereinigt war. Der Stichtag
  muss bei beiden Skripten derselbe sein, am besten der zuletzt importierte Tag (er war evtl. noch nicht fertig).

- **Import:** Jede Datei läuft in einer eigenen Transaktion. Ein Fehler in einer Datei macht nur diese Datei rückgängig.
  Der Import ist beliebig oft wiederholbar.
- **Bereinigung:** Von jeder Folge gleicher Werte bleibt nur die erste Zeile (`A, A, B, A, A` wird zu `A, B, A`). Die
  CSV-Sicherungen werden nicht verändert.

### 3.4 Auswertung – `fitnesspark_report.py`

```bash
.\venv\Scripts\python.exe fitnessparks\fitnesspark_report.py --open
```

Erzeugt `data/fitnesspark_auswertung.html` (Optionen: `--out DATEI`, `--open`). Die Seite lässt sich nach Park filtern
und zeigt Beste Zeit (Heatmap Wochentag × Uhrzeit), Tagesverlauf und Saison (Monatsmittel, Wochenverlauf, Monat ×
Uhrzeit). Die Diagramm-Bibliothek Plotly wird beim Öffnen aus dem Internet geladen.

**Auswertungsregeln:**

- Zeitraster von 5 Minuten. Ein Fenster gilt als gemessen, wenn mindestens ein Park eine Zeile geliefert hat.
- In einem gemessenen Fenster zählt ein Park ohne Zeile als leer (Belegung 0).
- Fenster ohne jede Messung (nachts, Ausfälle des Scrapers) und Tage ohne CSV-Datei werden nicht ausgewertet.
- Öffnungszeiten: Ein Fenster gilt für einen Park und Wochentag als geöffnet, wenn die Belegung an mindestens 80 % der
  gemessenen Tage grösser als 0 war.
- Monate mit weniger als 10 und Wochen mit weniger als 5 Tagen Daten fehlen in der Saison-Ansicht.

Die Auswertung liest bewusst die **CSV-Dateien** und nicht die Datenbank. Nur dort lässt sich unterscheiden, ob eine
fehlende Zeile „leer" oder „unverändert" bedeutet (siehe Entscheidungen).

---

## 4. CarRace (Autorennen mit KI)

Rennspiel mit pygame-ce. Alle Befehle im Ordner `CarRace` oder mit vollem Pfad (die Skripte wechseln selbst in ihren
Ordner).

```bash
.\venv\Scripts\python.exe CarRace\main_myrace.py
```

**Steuerung:** Pfeiltasten (Gas, Bremse, Lenken), **Enter** wechselt die Strecke und setzt die Autos zurück,
**Escape** beendet. Neben der Strasse wird das Auto langsamer.

### 4.1 Aufbau

| Datei | Aufgabe |
|---|---|
| `main_myrace.py` | Spiel: Fenster, Eingaben, Strecken, alle Autos |
| `car.py` | Auto: Position, Tempo, Richtung, Lenkwiderstand, Kollisionen |
| `constant.py` | Alle Zahlenwerte (Fenster, Physik, Aufholbonus, Farben der Strecke) |
| `ai.py` | Regelbasierte KI: drei Fühler, Überholen, Abstand halten, kleine Fahrfehler |
| `neural_ai.py` | Neuronales Netz (5 Fühler + Tempo → Lenkung, Gas), Speichern und Laden |
| `train_neural.py` | Training durch Auslese und Mutation (Neuroevolution) |
| `demo_neural.py` | Zuschauen: das gespeicherte Netz fährt ohne Spielerauto |
| `track_map.py` | Schnelle Streckenkarte (befahrbar, Fortschritt, Ziel) für Fühler und Training |
| `track_N.png` | Strecken; alle vorhandenen `track_1.png`, `track_2.png`, … werden geladen |

Im Spiel fahren der Spieler (rot), drei regelbasierte KI-Autos („vorsichtig", „mutig", „normal") und, falls ein
gespeichertes Netz existiert, ein lernendes Auto (rosa). Die KI-Autos starten nacheinander.

### 4.2 Fahrphysik

- Das Tempo ist durch `MAXSPEED` begrenzt (neben der Strasse mal `MALUSFACTOR`).
- Ab 80 % des Höchsttempos nimmt die Beschleunigung ab, beim Höchsttempo bleiben noch 10 %.
- **Lenkwiderstand:** Lenken kostet Tempo, anfangs wenig und mit der Dauer am Stück immer mehr. Ein enger Bogen ist also
  langsam, ein weiter Bogen schnell.
- **Aufholjagd:** Autos weit hinter dem Führenden bekommen ein höheres Tempolimit (bis +50 %), das nach dem Aufholen
  langsam wieder sinkt.
- Bei Zusammenstössen behalten beide Autos 40 % ihres Tempos.

### 4.3 Die lernende KI trainieren

```bash
.\venv\Scripts\python.exe CarRace\train_neural.py --races 30            # 30 Rennen ohne Fenster (schnell)
.\venv\Scripts\python.exe CarRace\train_neural.py --races 10 --show     # mit Fenster
.\venv\Scripts\python.exe CarRace\train_neural.py --fresh               # neu anfangen (altes Netz wird gesichert)
.\venv\Scripts\python.exe CarRace\train_neural.py --reset               # KI zurücksetzen (sichern und löschen)
.\venv\Scripts\python.exe CarRace\demo_neural.py --races 3 --cars 12    # zuschauen
```

Weitere Optionen von `train_neural.py`: `--population` (Autos pro Rennen, Standard 40), `--max-frames` (Höchstdauer eines
Rennens, Standard 1200), `--track` (Streckennummer).

**Ablauf:** Jedes Rennen ist eine Generation. Alle Autos starten gleichzeitig mit leicht abweichenden Netzen. Ein Auto
scheidet aus, wenn es die Strasse verlässt oder nicht mehr vorankommt. Danach werden die besten Netze behalten und
mutiert. Das beste Netz liegt in `CarRace/brains/best_brain.json` und wird beim nächsten Training und im Spiel wieder
verwendet. Der Ordner `brains/` gehört nicht ins Repository.

---

## 5. Wetterdaten (Weather)

Lädt die homogenen Monatsdaten aller MeteoSchweiz-Stationen (29 Klimastationen und 46 Niederschlagsstationen) über die
STAC-API von data.geo.admin.ch.

```bash
.env\Scripts\python.exe Weather\Init\Config_Generator.py   # einmalig: config.ini erzeugen (überschreibt nie)
.env\Scripts\python.exe Weather\GetWeatherData.py          # alle Stationen laden, CSV-Datei und Datenbank schreiben
```

- `GetWeatherData.py`: fragt die API je Datensatz ab, lädt die Monatsdatei jeder Station (Pause zwischen den Downloads,
  Zeitlimit 30 Sekunden) und speichert das Ergebnis im Ordner `Weather/daten/` (liegt nur lokal und steht in `.gitignore`):
  - `homogene_monatsdaten_JJJJMMTT_HHMMSS.csv`: alle Stationen in einer Datei, der Abrufzeitpunkt steht im Namen. Jeder
    Abruf erzeugt eine neue Datei, alte bleiben erhalten.
  - `weather.db` (SQLite): Tabelle `homogeneous_monthly` (Station, Monatserster, Parameter, Wert), dazu
    `stations` und `parameters` mit den Beschreibungen (Name, Originalkürzel, Einheit). Ein erneuter Abruf überschreibt gleiche
    Werte. Der Abrufzeitpunkt steht einmal in der Tabelle `meta` (Schlüssel `monthly_retrieved_at`). Die Tabellen werden bei
    Bedarf angelegt; eine ältere Datenbank mit `retrieved_at` in jeder Zeile wird beim nächsten Öffnen automatisch umgebaut.
    `homogeneous_monthly` ist `WITHOUT ROWID`, die Datenbank ist so nur noch etwa 45 statt 117 MB gross.
  - Schlägt der Download einer Station fehl, werden die übrigen trotzdem gespeichert; das Skript nennt die fehlenden
    Stationen und endet mit Exit-Code 1. Ein Abruf dauert rund zwei Minuten.
  - Die Downloads versuchen es je Adresse bis zu dreimal (mit wachsender Pause) und nutzen für TLS die klassische Kurve X25519.
    Grund: Mit Python 3.14 (OpenSSL 3.5) brach data.geo.admin.ch die Verbindung mit der Standardeinstellung zufällig ab
    (`SSL: UNEXPECTED_EOF_WHILE_READING`), mit X25519 klappte es zuverlässig.
- `ParameterNames.py`: ordnet den Kürzeln von MeteoSchweiz (z. B. `ths200m0`) sprechende Namen zu (`temp_2m_mean`). Die
  Namen gelten in CSV-Datei und Datenbank; das Originalkürzel steht in `parameters.code`. Unbekannte Kürzel bleiben
  unverändert.
- `temperatur_report.py`: erzeugt aus der Datenbank die interaktive Seite `Weather/daten/temperatur_auswertung.html` mit
  `temp_2m_mean` für eine wählbare Station: Jahresmittel als Abweichung von der Referenzperiode (1961–1990 oder
  1991–2020) mit Trend, Warming Stripes, Monatsmittel im Vergleich, Erwärmung je Monat und ein Vergleich aller Stationen.
  Es zählen nur Jahre mit zwölf Monatswerten. Die Seite lädt Plotly aus dem Internet. Aufruf:
  `py Weather	emperatur_report.py --open` (nach `GetWeatherData.py`).
- `Init/PrepareDB.py`: legt nur die Datenbank und die Tabellen an, ohne Abruf.
- `SqlLiteWD.py`: Klasse zum Schreiben in die SQLite-Datenbank, auch als `with`-Block nutzbar.
- `AzureMsSql.py`: Verbindung zu Azure SQL über Umgebungsvariablen (siehe Abschnitt 8).
- `config.ini`: Adresse der API, Datensätze, Dateiendung der Monatsdateien (`_m.csv`), Datenordner und Pause.

---

## 6. Stromstatistik (electricity)

`electricity/swiss_electricity.py` lädt die monatliche **Schweizerische Elektrizitätsbilanz** des Bundesamts für Energie (BFE,
Datensatz ogd35 auf opendata.swiss, Quelle: `https://www.bfe-ogd.ch/ogd35/ogd35_schweizerische_elektrizitaetsbilanz_monatswerte.csv`).
Die Datei enthält alle Monate seit Januar 2000 in GWh. Die jüngsten Monate sind provisorisch und werden vom BFE später korrigiert.

Aufruf (ohne Zusatzpakete, nur Standardbibliothek):

```bash
py electricity/swiss_electricity.py             # laden, speichern, Zusammenfassung ausgeben
py electricity/swiss_electricity.py --offline   # zuletzt gespeicherte CSV-Datei neu einlesen, ohne Download
py electricity/swiss_electricity.py --daten ORDNER   # anderer Ordner für CSV und Datenbank
```

Ergebnis im Ordner `electricity/daten/` (nicht im Repository):

- `elektrizitaetsbilanz_monatswerte_JJJJMMTT.csv`: die unveränderte Quelldatei vom Abruftag. Ältere Dateien bleiben liegen, so
  lassen sich Korrekturen der provisorischen Werte nachvollziehen.
- `electricity.db` (SQLite): Tabelle `monthly` mit einem Datensatz pro Monat (Neuladen aktualisiert bestehende Monate), Tabelle
  `abrufe` als Protokoll (neue und geänderte Monate pro Abruf) und die Sichten unten.

Enthaltene Grössen: Erzeugung nach Laufwerken, Speicherwerken, Kernkraft, Thermischen, Wind und Photovoltaik, `andere` (bis 2019,
damals nicht einzeln ausgewiesen), Landeserzeugung, Pumpstrom, Nettoerzeugung, Einfuhr, Ausfuhr, Landesverbrauch, Verluste und
Endverbrauch. Nicht ausgewiesene Werte sind `NULL`: Photovoltaik, Wind und Thermische gibt es erst seit 2020 getrennt.

**Über- und Unterproduktion:** `ueberschuss_gwh` = Nettoerzeugung minus Landesverbrauch. Das ist dasselbe wie Ausfuhr minus
Einfuhr. Positiv (`Ueberproduktion`) heisst, es wurde mehr erzeugt als verbraucht, negativ (`Unterproduktion`) heisst netto
importiert. `eigendeckung_pct` ist die Nettoerzeugung in Prozent des Landesverbrauchs.

| Sicht | Inhalt |
|---|---|
| `v_monat` | Monatswerte mit `wasserkraft_gwh`, Überschuss, Status, Eigendeckung und Anteilen von Wasserkraft, Kernkraft und Photovoltaik |
| `v_jahr` | Jahressummen, `vollstaendig` = 1 nur bei zwölf Monaten, Differenz zum Vorjahr |
| `v_halbjahr` | Winter (Oktober bis März, z. B. `Winter 2025/26`) und Sommer (April bis September) |
| `v_vorjahr` | jeder Monat neben demselben Vorjahresmonat, mit Differenz in GWh und Prozent |

Beispiel: Winterhalbjahre mit Über- oder Unterproduktion vergleichen:

```sql
SELECT halbjahr, ueberschuss_gwh, status, eigendeckung_pct FROM v_halbjahr WHERE typ = 'Winter' AND vollstaendig = 1;
```

Beim Einlesen werden die Rechenregeln der Quelle geprüft (Landeserzeugung = Summe der Kraftwerksarten, Nettoerzeugung =
Landeserzeugung minus Pumpstrom, Landesverbrauch = Nettoerzeugung plus Einfuhr minus Ausfuhr, Endverbrauch = Landesverbrauch
minus Verluste, Toleranz 3 GWh wegen Rundung). Abweichungen werden gemeldet, die Daten aber trotzdem gespeichert. Fehlen Spalten
oder ist die Datei leer, bricht der Abruf ab, bevor etwas überschrieben wird. Tests: `tests/test_swiss_electricity.py`.

---

## 7. Weitere Skripte

| Skript | Beschreibung |
|---|---|
| `mandelbaum.py` | Fenster mit Eingabefeldern für Ausschnitt und Iterationen. Berechnet Full HD mit numpy in rund 3 Sekunden, die Pixel sind quadratisch. |
| `matrix_simulation.py` | 100 Threads zählen je eine Zelle von 0 bis 9 hoch. Start, Stop, Reset. Das Fenster wird nur im Hauptthread aktualisiert. |
| `game_of_life.py` | Conways Game of Life (160 × 83 Zellen, das Fenster füllt einen FullHD-Monitor). Linke Maustaste halten setzt Zellen, rechte löscht sie, auch während die Simulation läuft. Leertaste: Start/Stop, `S` oder Pfeil rechts: genau ein Schritt, `C` löschen, `Z` Zufallsfeld, `T` Rand (Torus oder fest), `+`/`-` Tempo. Alle Funktionen gibt es auch als Knöpfe oben im Fenster. Aufruf: `python game_of_life.py`. |
| `Bingo.py` | Zieht Zahlen 1 bis 75, bis eine Reihe, Spalte oder Diagonale voll ist. Freies Feld in der Mitte, markierte Zahlen als `X`. |
| `JumpAndRun1.py` | Pfeile bewegen, Leertaste springt, Doppelsprung durch Loslassen und erneutes Drücken. |
| `run.py` / `sort.py` | Vergleicht Bubblesort, Shakersort und Quicksort (beide Varianten) auf drei Listen. `Sorting` zählt Vergleiche und Vertauschungen, Quicksort ist ebenfalls enthalten, als `quick_sort` (liefert eine neue Liste) und als `quick_sort_in_place` (tauscht wie Bubble- und Shakersort in der übergebenen Liste). Jedes Verfahren hat den Parameter `verbose` mit drei Stufen: `0` keine Ausgabe (Standard), `1` nur die Summen am Ende, zum Beispiel `Fertig: 2 Tausche, 4 Vergleiche` (bei Quicksort Verschiebungen), `2` zusätzlich jeder einzelne Tausch (bei Quicksort jede Verteilung auf die Listen kleiner, gleich und grösser), zum Beispiel `Sorting.bubble_sort(liste, verbose=2)`. |

---

## 8. Konfiguration und Geheimnisse

Zugangsdaten stehen **nie** im Code und nie im Repository. Sie werden aus Umgebungsvariablen gelesen:

| Variable | Verwendet in | Bedeutung |
|---|---|---|
| `AZURE_SQL_SERVER` | `Weather/AzureMsSql.py` | Servername |
| `AZURE_SQL_USER` | `Weather/AzureMsSql.py` | Benutzer |
| `AZURE_SQL_PASSWORD` | `Weather/AzureMsSql.py` | Passwort |
| `AZURE_SQL_DATABASE` | `Weather/AzureMsSql.py` | optional, sonst `AxjiDB1` |

Nicht im Repository (stehen in `.gitignore`): `venv/`, `.idea/`, `.vs/`, `__pycache__/`, `.env`, `*.db`, `data/` und
`CarRace/brains/`, `Weather/daten/` und `electricity/daten/`.

---

## 9. Arbeitsweise mit Git

- Repository: <https://github.com/Axji/Python>, Hauptzweig `master`.
- Änderungen laufen in der Regel über einen eigenen Branch und einen Pull Request. Kleine Einrichtungsänderungen (zum
  Beispiel `.vscode/`) können direkt auf `master`.
- Kommentare, Docstrings und Meldungen sind auf Deutsch geschrieben, mit Schweizer Schreibweise (`ss` statt `ß`).
- Die Git-Identität ist nur für dieses Repository gesetzt (nicht global).

---

## 10. Bekannte Einschränkungen

- Die Wetter-Auswertung schreibt noch nicht in die Datenbank (siehe 5).
- Die Abrufe der Fitnesspark-Website und von MeteoSchweiz hängen von deren Adressen ab. Ändern sich diese, brechen die
  Skripte ab. Die MeteoSchweiz-Adresse in `config.ini` verwendet `http` und sollte geprüft werden.
- Die Auswertung der Fitnesspark-Daten lädt Plotly aus dem Internet und ist offline nicht nutzbar.
- Automatische Tests gibt es für `sort.py`, `global_lib.py`, `game_of_life.py`, `jumprun1/` und `electricity/` (Ordner `tests/`). Die Skripte für Fitnesspark und Wetter sind nur von Hand geprüft.
