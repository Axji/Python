---
name: dokumentation-nachziehen
description: Zieht DOKUMENTATION.md nach, wenn sich Code, Skripte, Pakete, Befehle, Optionen, Umgebungsvariablen oder Ordner geändert haben. Einsetzen bei "Doku nachziehen", "Dokumentation aktualisieren", "ist die Doku noch aktuell", nach dem Mergen eines Pull Requests oder nach grösseren Code-Änderungen. Prüft jede Aussage gegen den Code und ändert nur, was nicht mehr stimmt. NICHT für Begründungen und Entscheidungen, dafür gibt es entscheidungen-eintragen.
---

# Dokumentation nachziehen

`DOKUMENTATION.md` beschreibt, **wie das Projekt funktioniert**: Einrichtung, Aufbau, Befehle, Optionen, Konfiguration.
Das **Warum** steht in `ENTSCHEIDUNGEN.md` und gehört nicht hierher.

## Vorgehen

1. **Änderungen finden.** Den letzten Commit bestimmen, der `DOKUMENTATION.md` berührt hat, und alles danach ansehen:
   ```bash
   git log -1 --format=%h -- DOKUMENTATION.md
   git log --oneline <hash>..HEAD
   git diff --stat <hash>..HEAD
   ```
   Fehlt ein Bezug (zum Beispiel bei einer neuen Anfrage "ist alles aktuell?"), das ganze Dokument prüfen.

2. **Abweichungen automatisch aufspüren.** Im Repo-Ordner ausführen (PowerShell):
   ```powershell
   $doc = Get-Content DOKUMENTATION.md -Raw
   "--- Skripte ohne Erwähnung:"
   git ls-files '*.py' | Where-Object { $_ -notmatch '__init__' } | ForEach-Object {
     if ($doc -notmatch [regex]::Escape((Split-Path $_ -Leaf))) { $_ } }
   "--- Kommandozeilen-Optionen ohne Erwähnung:"
   Select-String -Path (git ls-files '*.py') -Pattern 'add_argument\(["''](--[\w-]+)' |
     ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique |
     Where-Object { $doc -notmatch [regex]::Escape($_) }
   "--- Umgebungsvariablen ohne Erwähnung:"
   Select-String -Path (git ls-files '*.py') -Pattern 'environ(?:\.get\(|\[)["''](\w+)' |
     ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique |
     Where-Object { $doc -notmatch [regex]::Escape($_) }
   "--- Pakete aus requirements.txt ohne Erwähnung:"
   Get-Content requirements.txt | Where-Object { $_ -match '^[A-Za-z]' } |
     ForEach-Object { ($_ -split '[<>=]')[0] } | Where-Object { $doc -notmatch [regex]::Escape($_) }
   ```
   `SDL_VIDEODRIVER` ist ein bekannter Fehlalarm: `train_neural.py` setzt ihn selbst für den Betrieb ohne Fenster,
   es ist keine Einstellung des Benutzers und gehört nicht in die Doku.

   Umgekehrt gilt: Was in der Doku steht, aber im Repo nicht mehr existiert (gelöschte oder umbenannte Dateien,
   entfernte Optionen), muss raus oder angepasst werden. Dafür die in der Doku genannten Dateinamen mit
   `git ls-files` abgleichen.

3. **Jede betroffene Aussage am Code prüfen.** Nicht aus dem Gedächtnis oder aus dem alten Text übernehmen:
   - Befehle und Optionen: im Code nachlesen (`add_argument`, `__main__`-Block, Modul-Beschreibung).
   - Zahlen und Grenzwerte (Zeitlimits, Standardwerte, Anzahl Standorte): im Code zählen oder nachlesen.
   - Ordner und Dateien: mit `git ls-files` oder `Test-Path` bestätigen.
   - Pakete und Versionen: `requirements.txt`.
   - Ignorierte Ordner: `.gitignore`.
   Lässt sich etwas nicht prüfen, im Text als "bitte prüfen" kennzeichnen statt es zu behaupten.

4. **Nur ändern, was nicht mehr stimmt.** Die bestehende Gliederung, Tabellen und den Ton behalten. Neue Skripte in
   die Übersichtstabelle (Abschnitt 2) und in den passenden Fachabschnitt eintragen. Das Inhaltsverzeichnis anpassen,
   wenn sich Überschriften ändern.

5. **Prüfen und zeigen.** `git diff DOKUMENTATION.md` ausgeben und kurz zusammenfassen, was angepasst wurde.
   Die Schritte 2 und 3 danach noch einmal laufen lassen, bis keine Abweichung mehr gemeldet wird.

## Regeln

- **Sprache:** Deutsch mit Schweizer Schreibweise (`ss` statt `ß`), echte Umlaute (ä, ö, ü).
- **Keine zweite Dokumentation anlegen.** Es gibt genau eine `DOKUMENTATION.md`. Bestehendes pflegen.
- **Keine Geheimnisse** in die Doku: keine Passwörter, Tokens oder Serverdaten, nur die Namen der Umgebungsvariablen.
- **Kein Warum.** Steckt hinter der Änderung eine Entscheidung (neues Paket, andere Speicherung, geänderter Ablauf),
  nur das Ergebnis in die Doku schreiben und den Skill `entscheidungen-eintragen` anstossen oder dem Benutzer vorschlagen.
- **Nicht committen oder pushen**, ausser der Benutzer verlangt es ausdrücklich.
