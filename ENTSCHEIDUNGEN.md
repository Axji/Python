# Entscheidungen

Hier steht, **warum** etwas so gelöst ist, wie es ist. Wie das Projekt funktioniert, steht in
[DOKUMENTATION.md](DOKUMENTATION.md). Neue Einträge kommen **oben** an die Liste der jeweiligen Gruppe, mit fortlaufender
Nummer.

Quellen: `PR #n` verweist auf einen Pull Request in <https://github.com/Axji/Python>, Kurzhashes auf Commits. Wo der
Grund nur aus der Commit-Meldung bekannt ist, steht das dabei. Mit **Offen** markierte Einträge brauchen noch eine
Entscheidung oder Bestätigung.

## Inhalt

- [A. Sicherheit und Repository](#a-sicherheit-und-repository)
- [B. Fitnesspark-Daten](#b-fitnesspark-daten)
- [C. CarRace](#c-carrace)
- [D. Weitere Skripte und Fehlerbehebungen](#d-weitere-skripte-und-fehlerbehebungen)
- [E. Werkzeuge und Arbeitsweise](#e-werkzeuge-und-arbeitsweise)
- [Offene Punkte](#offene-punkte)
- [Vorlage für neue Einträge](#vorlage-für-neue-einträge)

---

## A. Sicherheit und Repository

### A1 – Zugangsdaten nur aus Umgebungsvariablen (2026-09-30, PR #2)
**Entscheidung:** Passwörter und Serverdaten stehen nie im Code. Sie werden aus Umgebungsvariablen gelesen
(`AZURE_SQL_*`). Fehlt eine Variable, bricht das Skript mit einer klaren Meldung ab.
**Grund:** Ein Datenbankpasswort lag im Klartext in einer Datei, und das Repository ist öffentlich.
**Folge:** Es gibt keine Passwort-Konstanten mehr. Die betroffene MariaDB existiert laut Besitzer nicht mehr, ein Ändern
des Passworts war deshalb nicht nötig.

### A2 – Passwort aus der Git-Historie entfernt (2026-09-30)
**Entscheidung:** Mit `git filter-repo` wurde das Passwort in allen alten Commits durch `***REMOVED***` ersetzt. Die drei
Branches (`master`, `cleanup/review-fixes`, `beautify-fitnesspark-script`) wurden per Force-Push neu geschrieben.
**Grund:** Ausdrücklicher Wunsch des Besitzers, obwohl die Datenbank nicht mehr existiert.
**Prüfung:** Die Dateistände (Tree-Hashes) aller Branches waren vor und nach dem Umschreiben identisch. Im ganzen Repo
gab es danach keinen Treffer mehr.
**Restrisiko:** Die alten Commits sind auf GitHub über die Pull-Request-Refs (`refs/pull/1/head`, `refs/pull/2/head`) und per
SHA noch abrufbar. Das lässt sich nur über den GitHub Support entfernen. Andere Klone und Forks haben noch die alte
Historie. Ein Backup mit dem alten Stand liegt unter `C:\dev\Phyton_backup_vor_historie.git`.
**Status:** Offen (siehe unten).

### A3 – Nur Quellcode versionieren (2026-09-30, PR #2)
**Entscheidung:** `venv/`, `.idea/`, `.vs/` und `__pycache__/` gehören nicht ins Repository. Die Abhängigkeiten stehen
in `requirements.txt`.
**Grund:** Die eingecheckte `venv` (8,5 MB) war an einen absoluten Pfad und Python 3.9 gebunden und damit nicht
portabel. Die `.pyc`-Dateien stammten von Python 3.4.
**Folge:** Nach jedem frischen Klon wird die `venv` mit `pip install -r requirements.txt` neu aufgebaut.

### A4 – Eigene Daten bleiben lokal (2026-10-01, PR #6, später 675b1c1)
**Entscheidung:** `data/` (CSV-Sicherungen und Datenbank) und `CarRace/brains/` (gelernte Netze) stehen in der
`.gitignore`. Die Beispiel-CSV wurde aus dem Repository entfernt.
**Grund:** Die Commit-Meldungen sagen nur „nur lokal". Vermutlich sind Messdaten und Trainingsstände persönlich und gross
(bitte bestätigen oder ergänzen).

---

## B. Fitnesspark-Daten

### B1 – SQLite statt MariaDB (2026-10-01, PR #4)
**Entscheidung:** Der Import läuft in eine lokale SQLite-Datei (`data/fitnessparks.db`). `fitnesspark_csv_to_mariadb.py`
wurde ersetzt durch `fitnesspark_csv_to_sqlite.py`.
**Grund:** Die MariaDB gibt es nicht mehr. SQLite braucht keinen Server und kein Passwort und gehört zur
Standardbibliothek.
**Folge:** `pymysql` entfällt, und damit auch jede Zugangsdaten-Konfiguration für diesen Teil.

### B2 – Ohne pandas (2026-10-01, PR #5)
**Entscheidung:** Der CSV-Import nutzt nur das `csv`-Modul der Standardbibliothek.
**Grund:** Die Commit-Meldung nennt „nur csv-Modul der Standardbibliothek". Vermutlich sollen die Abhängigkeiten klein
bleiben (bitte bestätigen).
**Folge:** `pandas` ist aus `requirements.txt` entfernt.

### B3 – CSV-Sicherung zusätzlich zur Datenbank (2026-10-01, PR #4)
**Entscheidung:** Der Scraper schreibt jede Messung doppelt: in die Tages-CSV und in die Datenbank. Ein Fehler in der
Datenbank lässt die CSV unberührt.
**Grund:** Die CSV-Dateien sind die unveränderte Rohdatenquelle. Die Datenbank wird bereinigt (B5), die CSV bleibt
vollständig.

### B4 – Wiederholbarer Import durch Eindeutigkeit (2026-10-01, PR #4)
**Entscheidung:** In der Tabelle `besucher` ist `(fitnesspark, Timestamp)` eindeutig, eingefügt wird mit
`INSERT OR IGNORE`. Jede CSV-Datei wird in einer eigenen Transaktion geladen.
**Grund:** Derselbe Import darf beliebig oft laufen, ohne doppelte Zeilen zu erzeugen. Ein Fehler in einer Datei darf
bereits geladene Dateien nicht verwerfen.
**Alternative (verworfen):** Ein Commit am Ende aller Dateien. Dabei verwarf ein Fehler auch die Zeilen früherer Dateien.

### B5 – Bereinigung löscht gleiche Folgewerte (2026-10-01, PR #4)
**Entscheidung:** Von jeder Folge gleicher Werte pro Park bleibt nur die erste Zeile (`A, A, B, A, A` → `A, B, A`).
Es gibt einen Testlauf mit `--dry-run`. Die CSV-Dateien werden nicht verändert.
**Grund:** Nicht ausdrücklich dokumentiert. Vermutlich soll die Datenbank nur Änderungen enthalten und klein bleiben
(bitte bestätigen).
**Folge:** In der Datenbank ist nicht mehr erkennbar, wie lange ein Wert galt. Deshalb nutzt die Auswertung (B6) die CSV.

### B6 – Auswertung aus den CSV-Dateien, als HTML mit Plotly (2026-10-01, PR #7)
**Entscheidung:** `fitnesspark_report.py` liest die CSV-Dateien und erzeugt eine eigenständige HTML-Seite. Die Diagramme
kommen aus der Bibliothek Plotly, die beim Öffnen aus dem Internet geladen wird. Es sind keine Python-Zusatzpakete nötig.
**Grund:** Der Scraper speichert nur Werte grösser als 0. Ob eine fehlende Zeile „Belegung 0" oder „unverändert" heisst,
lässt sich nur mit den ursprünglichen CSV-Dateien erkennen.
**Regeln:** 5-Minuten-Raster. Ein Fenster gilt als geöffnet, wenn die Belegung an mindestens 80 % der gemessenen Tage
grösser als 0 war. Monate mit weniger als 10 und Wochen mit weniger als 5 Tagen Daten werden weggelassen.
**Nachteil:** Offline funktioniert die Seite nicht.

### B7 – Tippfehler im Dateinamen korrigiert (2026-10-01, a093a9d)
**Entscheidung:** `Fitnespark_Belegung_…csv` heisst jetzt `Fitnesspark_Belegung_…csv`.
**Folge:** Import und Auswertung lesen alle `*.csv` im Ordner `data`, alte und neue Dateinamen funktionieren also beide.

### B8 – Scraper robuster gemacht (2026-09-30, PR #2)
**Entscheidung:** Zeitlimit von 15 Sekunden je Abruf. Die Kopfzeile der CSV wird einmal pro Lauf geschrieben statt pro
Park. Bei der Fehlerbehandlung steht `ValueError` vor `RequestException`.
**Grund:** Ohne Zeitlimit kann ein Abruf ewig hängen. `requests.exceptions.JSONDecodeError` erbt von beiden Klassen, mit
der umgekehrten Reihenfolge wäre die Meldung „kein gültiges JSON" nie erschienen.
**Sihlcity:** Die Park-`ID` wurde von 784 auf 704 geändert, passend zur URL (`park_id=704`), mit der bisher Daten gesammelt
wurden. Das wurde nicht ausdrücklich bestätigt.

---

## C. CarRace

### C1 – Zwei Stufen von KI (2026-10-02, PR #8 und #9)
**Entscheidung:** Es gibt eine regelbasierte KI (`ai.py`: drei Fühler, Überholen, Abstand halten, zufällige kleine
Fehler) und eine lernende (`neural_ai.py`, `train_neural.py`).
**Grund:** Die regelbasierte KI liefert sofort Gegner mit unterschiedlichem Fahrstil. Die lernende zeigt, wie ein Netz
fahren lernt, und tritt im Spiel als weiteres Auto an.

### C2 – Lernen durch Auslese und Mutation (2026-10-02, c0181da)
**Entscheidung:** Das Netz (5 Fühler + Tempo → Lenkung und Gas, 8 versteckte Neuronen) lernt durch Neuroevolution, nicht
durch Rückwärtsrechnen. Die besten Netze bleiben, werden mutiert und ergänzt um zufällige Neulinge.
**Grund:** Die Modul-Beschreibung nennt es ein „einfaches neuronales Netz" ohne Rückwärtsrechnen. Vermutlich war Einfachheit
ohne Zusatzbibliothek das Ziel (bitte bestätigen).
**Folge:** Das Training ist zufallsabhängig. Startposition und -richtung werden leicht variiert, damit das Gelernte
robuster ist.

### C3 – Fahrphysik so abgestimmt, dass Tempo etwas kostet (2026-10-02, 94dfc06, 7eecc31, ea69388)
**Entscheidung:** Ab 80 % des Höchsttempos nimmt die Beschleunigung ab (beim Höchsttempo noch 10 %). Lenken kostet Tempo,
mit der Dauer am Stück immer mehr. Autos weit hinter dem Führenden bekommen einen Aufholbonus von bis zu 50 %.
**Grund:** Laut den Kommentaren in `constant.py` soll der Höchstwert schwerer zu erreichen sein, und enge Kurven sollen
langsamer sein als weite. Der Aufholbonus soll Autos weit hinten wieder heranführen.
**Folge:** Alle Werte stehen in `constant.py` und lassen sich dort einstellen.

### C4 – Streckenkarte statt Pixelabfrage (2026-10-02)
**Entscheidung:** Aus dem Streckenbild wird einmal eine Karte berechnet (befahrbar, Fortschritt, Ziel), die die Fühler
und das Training nutzen (`track_map.py`).
**Grund (laut Modul-Beschreibung):** Fühler und Rennbewertung sind deutlich schneller als mit `Surface.get_at()`.

### C5 – KI zurücksetzen sichert, statt zu löschen (2026-10-02, e008ffd)
**Entscheidung:** `--reset` und `--fresh` kopieren das alte Netz mit Zeitstempel nach `brains/`, bevor sie es ersetzen.
**Grund:** Vermutlich soll ein Training nicht durch eine Fehleingabe verloren gehen (bitte bestätigen).

### C6 – Fehler im Spiel behoben (2026-09-30, PR #2)
**Entscheidung:** ESC und das Schliessen-Kreuz beenden das Spiel sauber. Fährt das Auto aus dem Bild, gilt das als
„neben der Strasse" statt als Absturz. Das Modul `car` wird nicht mehr von einer Schleifenvariable überdeckt.
**Folge:** `main_myrace_1,9.py` heisst jetzt `main_myrace.py` (ein Komma im Namen macht eine Datei nicht importierbar).
Das Spiel wechselt selbst in seinen Ordner und lädt die Bilder von dort.

---

## D. Weitere Skripte und Fehlerbehebungen

### D1 – Skripte löschen und überschreiben nie stillschweigend (2026-09-30, PR #2)
**Entscheidung:** `PrepareDB.py` nutzt `CREATE TABLE IF NOT EXISTS` statt `DROP TABLE`. `Config_Generator.py` öffnet die
Datei im Modus „nur neu anlegen" und bricht ab, wenn `config.ini` schon existiert.
**Grund:** Beim ersten Lauf brach `DROP TABLE` ab, bei jedem späteren Lauf löschte es alle Daten. Der Generator
überschrieb die funktionierende Konfiguration mit unvollständigen Werten.

### D2 – Pfade relativ zur Skriptdatei, kein Code beim Import (2026-09-30, PR #2)
**Entscheidung:** Pfade werden aus `__file__` gebildet (`os.path.join`), und Skripte starten ihre Arbeit nur unter
`if __name__ == "__main__":`.
**Grund:** Vorher liefen Skripte nur aus dem richtigen Ordner. `'..\daten\weather.db'` enthält zudem eine ungültige
Escape-Sequenz (ab Python 3.12 eine Warnung). Ein Import hat vorher Spiele und Downloads gestartet.

### D3 – Tk nur im Hauptthread (2026-09-30, PR #2)
**Entscheidung:** In `matrix_simulation.py` ändern die Zell-Threads nur Daten (unter einem Lock). Die Anzeige wird per
`root.after` im Hauptthread aktualisiert. Gestoppt wird über ein `Event`, das auch wartende Threads sofort weckt.
**Grund:** Tk ist nicht thread-sicher, das führte zu Hängern. Ein erneuter Start innerhalb von 2 Sekunden erzeugte doppelte
Threads.
**Folge:** `test.py` heisst jetzt `matrix_simulation.py`. Unter dem alten Namen hätte `pytest` die Datei importiert und
ein Fenster geöffnet.

### D4 – Mandelbrot mit numpy und quadratischen Pixeln (2026-09-30, PR #2)
**Entscheidung:** Die Berechnung läuft vektorisiert mit numpy. Der y-Bereich ist ±0,84375 (Seitenverhältnis 16:9).
**Grund:** Die Schleife in reinem Python brauchte Minuten und blockierte das Fenster. Mit x-Bereich 3 und y-Bereich 2 war
das Bild verzerrt.
**Prüfung:** Auf einem 160×90-Raster gleicht das Ergebnis der alten Berechnung pixelgenau. Full HD braucht rund 3 Sekunden.

### D5 – Download und Datei-Umgang in `GetWeatherData.py` (2026-09-30, PR #2)
**Entscheidung:** Antworten werden mit `.decode('utf-8')` gelesen, Dateien mit `with` geschrieben, Abrufe haben ein
Zeitlimit von 30 Sekunden, und nur Dateinamen im Muster `JJJJ-MM-TT_…txt` zählen.
**Grund:** `str(bytes)` erzeugte `b'…'`-Text mit zerstörten Umlauten, die Datei wurde nie geschlossen, und eine fremde
Datei im Datenordner liess `parse_files()` abstürzen.

---

## E. Werkzeuge und Arbeitsweise

### E1 – Python 3.13 (2026-09-30)
**Entscheidung:** Das Projekt läuft mit Python 3.13 (getestet mit 3.13.15), `requirements.txt` hat Ober- und Untergrenzen.
**Grund:** Die alte `venv` nutzte Python 3.9, dessen Support laut Python-Releaseplan Ende 2025 endete. Aktuelles pandas
und numpy brauchen mindestens Python 3.11 bzw. 3.12. Alle Pakete installieren sich auf 3.13, `pip check` meldet keine
Konflikte.
**Status:** Python 3.14 (3.14.7) ist verfügbar, es wurde noch nicht umgestellt (siehe Offene Punkte).

### E2 – VS Code mit Ruff (2026-10-03, a3a2abf)
**Entscheidung:** Editor ist VS Code mit den Erweiterungen Python, Pylance, Ruff und Jupyter. Die Einstellungen liegen in
`.vscode/` im Repository und zeigen auf die `venv`. Ruff formatiert beim Speichern und sortiert die Imports.
**Grund:** VS Code war schon installiert, ein zweiter Editor bringt wenig. PyCharm Community bleibt eine gleichwertige
Alternative.
**Weg:** `.vscode/` wurde direkt auf `master` committet, ohne Pull Request.

### E3 – Änderungen über Branch und Pull Request (seit 2026-09-30)
**Entscheidung:** Inhaltliche Änderungen laufen über einen eigenen Branch und einen Pull Request, den der Besitzer auf
GitHub selbst mergt. Kleine Einrichtungsänderungen dürfen direkt auf `master`.
**Grund:** Der Pull Request ist der Moment zum Prüfen. Bis PR #9 sind die Änderungen so jeweils einzeln nachvollziehbar
geblieben.

### E4 – Kommentare und Meldungen auf Deutsch (2026-09-30, PR #3)
**Entscheidung:** Kommentare, Docstrings und Ausgaben sind deutsch, mit Schweizer Schreibweise (`ss` statt `ß`).
**Grund:** Die Commit-Meldung nennt keinen. Vermutlich soll der Code ohne Übersetzen lesbar sein (bitte bestätigen).

---

## Offene Punkte

| Punkt | Was fehlt | Von |
|---|---|---|
| Alte Commits auf GitHub | Beim GitHub Support das Löschen der gecachten Commits und der Pull-Request-Refs beantragen (A2) | Besitzer |
| Backup mit altem Passwort | `C:\dev\Phyton_backup_vor_historie.git` löschen, sobald nichts mehr gebraucht wird | Besitzer |
| Python 3.14 | Entscheiden, ob umgestellt wird. Der Versuch, es parallel zu installieren, schlug mit Fehler 1638 („andere Version bereits installiert") fehl. Vorher prüfen, ob alle Pakete (besonders `pygame` und `pymssql`) Wheels für 3.14 haben | Besitzer |
| Sihlcity-ID | Bestätigen, dass `704` (URL) richtig ist und nicht `784` | Besitzer |
| Wetterdaten | `parse_content` schreibt noch nichts in die Datenbank | Besitzer |
| MeteoSchweiz-Adresse | `http://…` in `config.ini` prüfen (Weiterleitung, `https`) | Besitzer |
| Lokaler Branch | `cleanup/review-fixes` ist gemergt und auf GitHub gelöscht, lokal noch vorhanden | Besitzer |
| `pymssql` | Steht in `requirements.txt`, wird aber nur von `AzureMsSql.py` genutzt, das nirgends aufgerufen wird. Entfernen oder nutzen | Besitzer |
| pygame | `pygame` 2.6.1 ist von 2024. `pygame-ce` ist der aktiv gepflegte Fork mit gleichem `import pygame`, nicht geprüft | Besitzer |

---

## Vorlage für neue Einträge

```markdown
### X1 – Kurztitel (Datum, PR #n)
**Entscheidung:** Was gilt jetzt?
**Grund:** Warum? Welches Problem wurde gelöst?
**Alternative (verworfen):** Was wurde nicht gewählt und warum?
**Folge:** Was ändert sich dadurch? Was ist offen?
```
