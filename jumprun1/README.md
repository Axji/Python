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
| R | nach Spielende neu starten |
| Esc | beenden |

## Spielregeln

- Ziel ist die Fahne am Ende des Plans (die Zielzone reicht bis zum oberen Rand, man kann sie nicht überspringen).
- Münzen geben 10 Punkte. **Fragezeichen-Blöcke:** von unten anspringen, dann fällt eine Münze heraus (10 Punkte, 3 Münzen je Block, danach ist der Block leer). Gegner lassen sich abschiessen (100 Punkte) oder von oben anspringen (200 Punkte).
- Ein Treffer von der Seite oder ein Sturz in ein Loch kostet ein Leben (3 Leben). Nach einem Treffer ist die Figur kurz geschützt.

## Aufbau

| Datei | Inhalt |
|---|---|
| `main.py` | Startpunkt |
| `game.py` | Spielschleife, Regeln, Kamera, Zeichnen |
| `entities.py` | Spielfigur (Laufen, Springen, Schiessen), Gegner, Kugeln und die gemeinsame Kollisionsphysik |
| `level.py` | Der Spielplan als Raster (`build_grid()`), Kollisionsflächen und Startpunkte |
| `pixelart.py` | Textbilder der Figuren, Kacheln und der scrollende Hintergrund |
| `constants.py` | Alle Zahlenwerte (Tempo, Sprunghöhe, Schussabstand, Leben ...) |

Die Tests liegen in `tests/test_jumprun1.py` (laufen ohne Fenster).

## Anpassen

- **Spielplan ändern:** in `level.py` die Funktion `build_grid()` bearbeiten. Zeichen: `#` Erde, `B` Ziegel, `?` Block, `P` Start,
  `E` Gegner, `C` Münze, `F` Ziel. Löcher stehen in `GAPS`.
- **Figur neu zeichnen:** die Textbilder `PLAYER_BODY` und `PLAYER_LEGS` in `pixelart.py` ändern (jedes Zeichen ist ein Pixel,
  Farben in `PALETTE`).
- **Spielgefühl ändern:** Werte in `constants.py`, zum Beispiel `JUMP_SPEED`, `RUN_MAX` oder `SHOOT_COOLDOWN`.

## Noch offen (Ideen für den Ausbau)

- Die Fragezeichen-Blöcke geben nur Münzen her, keine anderen Überraschungen (Pilz, Waffen-Upgrade ...).
- Nur ein Gegnertyp, keine Gegner, die zurückschiessen.
- Kein Ton, kein Titelbildschirm, nur ein Plan.
