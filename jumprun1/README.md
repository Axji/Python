# jumprun1

Grundgerüst für ein Jump-and-Run im Stil von Giana Sisters und Super Mario (pygame-ce). Die Spielfläche ist 320 x 180
Pixel gross und wird vierfach vergrössert, dadurch sieht alles pixelig aus. Es werden keine Bilddateien geladen:
Figur, Gegner, Kacheln und Hintergrund entstehen beim Start aus Textbildern und einfachen Zeichenbefehlen.

## Starten

```bash
python jumprun1/main.py
```

Voraussetzung: `pip install -r requirements.txt` (pygame-ce).

## Steuerung

| Taste | Aktion |
|---|---|
| Pfeil links/rechts oder A/D | laufen |
| Leertaste, Pfeil hoch oder W | springen (länger gedrückt = höher). **Doppelsprung:** in der Luft noch einmal drücken, danach erst landen |
| X, J oder Strg | **geradeaus nach vorne schiessen** (gedrückt halten = Dauerfeuer) |
| R | **Reset 1:** aktuelles Level neu starten, mit 3 Leben und 0 Punkten (jederzeit) |
| N | **Reset 2:** neues Spiel ab Level 1, mit 3 Leben und 0 Punkten (jederzeit) |
| Enter | nach einem geschafften Level: weiter zum nächsten |
| Esc | beenden |

## Spielregeln

- Nach Level 1 folgen endlos neue, zufällig erzeugte Level (Enter nach dem Ziel). Punkte und Leben bleiben; nach Game Over beginnt das Spiel wieder bei Level 1.
- Ziel ist die Fahne am Ende des Plans (die Zielzone reicht bis zum oberen Rand, man kann sie nicht überspringen).
- Münzen geben 10 Punkte. **Fragezeichen-Blöcke:** von unten anspringen, dann fällt eine Münze heraus (10 Punkte, 3 Münzen je Block, danach ist der Block leer). Gegner lassen sich abschiessen (100 Punkte) oder von oben anspringen (200 Punkte).
- Ein Treffer von der Seite oder ein Sturz in ein Loch kostet ein Leben (3 Leben). Nach einem Treffer ist die Figur kurz geschützt.

## Aufbau

| Datei | Inhalt |
|---|---|
| `main.py` | Startpunkt |
| `game.py` | Spielschleife, Regeln, Kamera, Zeichnen |
| `entities.py` | Spielfigur (Laufen, Springen, Schiessen), Gegner, Kugeln und die gemeinsame Kollisionsphysik |
| `level.py` | Der Spielplan von Level 1 als Raster (`build_grid()`), Kollisionsflächen und Startpunkte |
| `levelgen.py` | Zufälliger Level-Generator für Level 2 und alle weiteren (siehe unten) |
| `reach.py` | Misst mit der echten Physik, wie weit und hoch Einzel- und Doppelsprung kommen |
| `pixelart.py` | Textbilder der Figuren, Kacheln und der scrollende Hintergrund |
| `constants.py` | Alle Zahlenwerte (Tempo, Sprunghöhe, Schussabstand, Leben ...) |

Die Tests liegen in `tests/test_jumprun1.py` (laufen ohne Fenster).

## Level-Generator

Level 2, 3, ... entstehen aus einem Zufallswert (pro Spiel neu) in `levelgen.generate_grid(seed, number)`. Jedes ist
**doppelt so lang wie Level 1** (160 Spalten). Garantien, die in `tests/test_jumprun1.py` geprüft werden:

- Die Schwierigkeit steigt mit dem Level (bis Level 10): In Level 2 gehen rund 70 % der Hindernisse mit dem Einzelsprung, in Level 10 nur noch rund 20 %, und die Lücken werden breiter. Drops mit verzögertem Doppelsprung gibt es ab Level 3.
- Keine Lücke und keine Stufe ist grösser, als der Doppelsprung schafft.
- Es gibt Lücken und Mauern, die der Einzelsprung nicht schafft (Doppelsprung nötig), daneben auch leichte Stellen.
- Es gibt **Drops**: eine tiefer liegende Landung hinter einer sehr breiten Lücke. Dort reicht der zweite Sprung im höchsten
  Punkt nicht, man muss ihn **verzögert im Fallen** auslösen, um die Strecke maximal auszunutzen.
- Ziegel und Blöcke liegen weit weg von den Plattformkanten und behindern keinen Absprung.

Die Reichweiten stehen in `levelgen.REACH` und wurden mit `reach.py` an der echten Physik gemessen. Ändert man die Sprung-
werte in `constants.py`, schlagen die Tests `test_reach_table_*` an: dann die Tabelle neu messen (`reach.max_gap`).

## Anpassen

- **Spielplan ändern:** in `level.py` die Funktion `build_grid()` bearbeiten. Zeichen: `#` Erde, `B` Ziegel, `?` Block, `P` Start,
  `E` Gegner, `C` Münze, `F` Ziel. Löcher stehen in `GAPS`.
- **Figur neu zeichnen:** die Textbilder `PLAYER_BODY` und `PLAYER_LEGS` in `pixelart.py` ändern (jedes Zeichen ist ein Pixel,
  Farben in `PALETTE`).
- **Spielgefühl ändern:** Werte in `constants.py`, zum Beispiel `JUMP_SPEED`, `RUN_MAX` oder `SHOOT_COOLDOWN`.

## Noch offen (Ideen für den Ausbau)

- Die Fragezeichen-Blöcke geben nur Münzen her, keine anderen Überraschungen (Pilz, Waffen-Upgrade ...).
- Nur ein Gegnertyp, keine Gegner, die zurückschiessen.
- Kein Ton, kein Titelbildschirm.

## Als .exe bauen (Windows)

Mit PyInstaller entsteht eine einzelne `JumpRun.exe`, die ohne installiertes Python läuft. Im Ordner `C:\dev\python`:

```bash
.\venv\Scripts\python.exe -m pip install pyinstaller
.\venv\Scripts\pyinstaller.exe JumpRun.spec
```

Die fertige Datei liegt danach in `dist\JumpRun.exe`. Die Einstellungen (ohne Konsolenfenster, eine einzelne Datei) stehen in
`JumpRun.spec`. Die Ordner `build/` und `dist/` sind in der `.gitignore`, die `.exe` kommt also nicht ins Repository.
