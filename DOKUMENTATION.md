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
6. [Weitere Skripte](#6-weitere-skripte)
7. [Konfiguration und Geheimnisse](#7-konfiguration-und-geheimnisse)
8. [Arbeitsweise mit Git](#8-arbeitsweise-mit-git)
9. [Bekannte Einschränkungen](#9-bekannte-einschränkungen)

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

**Pakete** (`requirements.txt`): `requests`, `numpy`, `pillow`, `pygame`, `pymssql`. Alles andere (SQLite, CSV, Tkinter)
gehört zur Standardbibliothek von Python.

**VS Code:** Der Ordner `.vscode/` enthält die Einstellungen. Der Interpreter zeigt auf `venv`, Ruff formatiert beim
Speichern und sortiert die Imports. Mit **F5** wird die geöffnete Datei im Debugger gestartet. Empfohlene
Erweiterungen: Python, Pylance, Ruff, Jupyter.

**Prüfen:** Die Ruff-Regeln stehen in `pyproject.toml`. Lint und Tests laufen so (auch in GitHub Actions, `.github/workflows/ci.yml`):

```bash
.envScriptspython.exe -m pip install ruff pytest
.envScriptsuff.exe check .
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
| `CarRace/` | Autorennen mit regelbasierter und lernender KI | pygame |
| `Weather/` | Klimadaten von MeteoSchweiz laden, SQLite-Ablage | – |
| `mandelbaum.py` | Mandelbrot-Generator mit Fenster | numpy, pillow |
| `matrix_simulation.py` | 10×10-Matrix, jede Zelle zählt in einem eigenen Thread | – |
| `Bingo.py`, `JumpAndRun1.py` | Kleine Spiele | pygame (JumpAndRun) |
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
```

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

Rennspiel mit pygame. Alle Befehle im Ordner `CarRace` oder mit vollem Pfad (die Skripte wechseln selbst in ihren
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

Lädt monatliche Klimadaten von MeteoSchweiz.

```bash
.\venv\Scripts\python.exe Weather\Init\Config_Generator.py   # einmalig: config.ini erzeugen (überschreibt nie)
.\venv\Scripts\python.exe Weather\Init\PrepareDB.py          # SQLite-Datenbank und Tabelle anlegen
.\venv\Scripts\python.exe Weather\GetWeatherData.py          # Dateien auswerten
```

- `GetWeatherData.py`: `get_files_from_web()` lädt je Station eine Textdatei nach `Weather/daten/` (liegt nur lokal und steht in `.gitignore`; Dateiname
  `JJJJ-MM-TT_Station.txt`, Pause zwischen den Downloads, Zeitlimit 30 Sekunden). `parse_files()` liest die Dateien des
  neuesten Datums. Beim Start ist der Download-Aufruf auskommentiert.
- `SqlLiteWD.py`: Klasse zum Schreiben in die SQLite-Tabelle `weather`, auch als `with`-Block nutzbar.
- `AzureMsSql.py`: Verbindung zu Azure SQL über Umgebungsvariablen (siehe Abschnitt 7).
- `config.ini`: Adressen, Datenordner und Textmarken für die Auswertung.

**Stand:** Das Auswerten der Dateien (`parse_content`) schreibt noch nichts in die Datenbank. Der Teil ist vorbereitet,
aber nicht umgesetzt.

---

## 6. Weitere Skripte

| Skript | Beschreibung |
|---|---|
| `mandelbaum.py` | Fenster mit Eingabefeldern für Ausschnitt und Iterationen. Berechnet Full HD mit numpy in rund 3 Sekunden, die Pixel sind quadratisch. |
| `matrix_simulation.py` | 100 Threads zählen je eine Zelle von 0 bis 9 hoch. Start, Stop, Reset. Das Fenster wird nur im Hauptthread aktualisiert. |
| `Bingo.py` | Zieht Zahlen 1 bis 75, bis eine Reihe, Spalte oder Diagonale voll ist. Freies Feld in der Mitte, markierte Zahlen als `X`. |
| `JumpAndRun1.py` | Pfeile bewegen, Leertaste springt, Doppelsprung durch Loslassen und erneutes Drücken. |
| `run.py` / `sort.py` | Vergleicht Bubblesort und Shakersort auf drei Listen. `Sorting` zählt Vergleiche und Vertauschungen, Quicksort ist ebenfalls enthalten. |

---

## 7. Konfiguration und Geheimnisse

Zugangsdaten stehen **nie** im Code und nie im Repository. Sie werden aus Umgebungsvariablen gelesen:

| Variable | Verwendet in | Bedeutung |
|---|---|---|
| `AZURE_SQL_SERVER` | `Weather/AzureMsSql.py` | Servername |
| `AZURE_SQL_USER` | `Weather/AzureMsSql.py` | Benutzer |
| `AZURE_SQL_PASSWORD` | `Weather/AzureMsSql.py` | Passwort |
| `AZURE_SQL_DATABASE` | `Weather/AzureMsSql.py` | optional, sonst `AxjiDB1` |

Nicht im Repository (stehen in `.gitignore`): `venv/`, `.idea/`, `.vs/`, `__pycache__/`, `.env`, `*.db`, `data/` und
`CarRace/brains/`.

---

## 8. Arbeitsweise mit Git

- Repository: <https://github.com/Axji/Python>, Hauptzweig `master`.
- Änderungen laufen in der Regel über einen eigenen Branch und einen Pull Request. Kleine Einrichtungsänderungen (zum
  Beispiel `.vscode/`) können direkt auf `master`.
- Kommentare, Docstrings und Meldungen sind auf Deutsch geschrieben, mit Schweizer Schreibweise (`ss` statt `ß`).
- Die Git-Identität ist nur für dieses Repository gesetzt (nicht global).

---

## 9. Bekannte Einschränkungen

- Die Wetter-Auswertung schreibt noch nicht in die Datenbank (siehe 5).
- Die Abrufe der Fitnesspark-Website und von MeteoSchweiz hängen von deren Adressen ab. Ändern sich diese, brechen die
  Skripte ab. Die MeteoSchweiz-Adresse in `config.ini` verwendet `http` und sollte geprüft werden.
- Die Auswertung der Fitnesspark-Daten lädt Plotly aus dem Internet und ist offline nicht nutzbar.
- Automatische Tests gibt es nur für `sort.py` und `global_lib.py` (Ordner `tests/`). Die Skripte für Spiele, Fitnesspark und Wetter sind nur von Hand geprüft.
