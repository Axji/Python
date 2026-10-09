# Python

Sammlung eigener Python-Projekte und Übungen (Python 3.13).

```bash
pip install -r requirements.txt
```

## Projekte

| Ordner / Datei | Inhalt |
|---|---|
| `CarRace/` | Autorennen mit pygame (`main_myrace.py`) und einer lernenden KI. `train_neural.py` trainiert ein neuronales Netz per Auslese und Mutation, `demo_neural.py` zeigt es. Gelernte Netze liegen lokal in `CarRace/brains/` und sind nicht im Repo. |
| `Fitnesspark_belegung.py`, `fitnesspark_db.py`, `fitnessparks/` | Liest die Auslastung der Fitnesspark-Standorte aus, speichert sie als CSV und in SQLite, bereinigt die Daten (`fitnesspark_clean.py`) und erzeugt eine HTML-Auswertung (`fitnesspark_report.py`). Die Daten liegen in `data/` und sind nicht im Repo. |
| `Weather/` | Lädt Klimadaten von MeteoSchweiz, speichert sie in SQLite (`SqlLiteWD.py`) oder Azure SQL (`AzureMsSql.py`, Zugangsdaten über die Umgebungsvariablen `AZURE_SQL_SERVER`, `AZURE_SQL_USER`, `AZURE_SQL_PASSWORD`). |
| `Bingo.py` | Bingo-Simulation |
| `JumpAndRun1.py` | Einfaches Jump-and-Run mit pygame (Pfeiltasten, Leertaste, Doppelsprung) |
| `mandelbaum.py` | Mandelbrot-Generator mit tkinter-Fenster |
| `matrix_simulation.py` | 10x10-Matrix, in der jede Zelle in einem eigenen Thread zählt |
| `sort.py`, `run.py`, `global_lib.py` | Sortieralgorithmen (Bubblesort, Shakersort) mit Demo in `run.py` |

Jedes Skript hat am Anfang eine Beschreibung mit Aufruf und Steuerung.
