---
name: entscheidungen-eintragen
description: Trägt wichtige Anpassungen und Entscheidungen mit Grund in ENTSCHEIDUNGEN.md ein. Einsetzen bei "halte das fest", "Entscheidung eintragen", "ENTSCHEIDUNGEN.md aktualisieren", nach dem Wechsel eines Pakets, einer Datenbank, eines Werkzeugs oder Ablaufs, nach Sicherheits- und Datenablage-Entscheidungen und nach dem Merge eines Pull Requests mit grundlegenden Änderungen. NICHT für Bedienung und Aufbau (dafür dokumentation-nachziehen) und nicht für Kleinkram wie Tippfehler oder Formatierung.
---

# Entscheidungen eintragen

`ENTSCHEIDUNGEN.md` hält fest, **warum** etwas so gelöst ist. Das **Wie** (Befehle, Aufbau) steht in
`DOKUMENTATION.md`.

## Was ist eintragswürdig?

Eintragen, wenn die Änderung eine **Wahl zwischen Alternativen** war, die später jemand hinterfragen könnte:

- Wechsel von Paket, Datenbank, Dateiformat oder Werkzeug (zum Beispiel MariaDB zu SQLite)
- Sicherheit: Umgang mit Zugangsdaten, Historie, öffentlichen Daten
- Was im Repository liegt und was lokal bleibt (`.gitignore`)
- Verhalten, das auf einer Regel beruht (Auswertungsregeln, Bereinigung, Grenzwerte)
- Arbeitsweise (Branches, Pull Requests, Editor, Sprache)
- Bewusst verworfene Wege, damit sie nicht erneut vorgeschlagen werden

**Nicht eintragen:** Tippfehler, reine Formatierung, Umbenennen ohne Hintergrund, Fehlerbehebungen ohne
Designentscheidung (die stehen in der Git-Historie).

## Vorgehen

1. **Quelle sammeln.** `git log --oneline -20`, den Diff und, falls vorhanden, die Pull-Request-Beschreibung lesen
   (`gh pr view <nr> --repo Axji/Python`). Dazu `ENTSCHEIDUNGEN.md` lesen, um Doppelungen zu vermeiden.

2. **Prüfen, ob es schon einen Eintrag gibt.** Betrifft die Änderung eine bestehende Entscheidung, diese
   fortschreiben oder als überholt markieren, kein zweiter Eintrag zum selben Thema.

3. **Gruppe und Nummer wählen.** Gruppen: **A** Sicherheit und Repository, **B** Fitnesspark-Daten, **C** CarRace,
   **D** Weitere Skripte und Fehlerbehebungen, **E** Werkzeuge und Arbeitsweise. Neue Einträge kommen **ans Ende der
   Gruppe** mit der nächsten freien Nummer (zum Beispiel nach B8 kommt B9). Passt keine Gruppe, den Benutzer fragen,
   bevor eine neue angelegt wird.

4. **Eintrag schreiben** in dieser Form:
   ```markdown
   ### B9 – Kurztitel (JJJJ-MM-TT, PR #n oder Kurzhash)
   **Entscheidung:** Was gilt jetzt?
   **Grund:** Warum? Welches Problem wurde gelöst?
   **Alternative (verworfen):** Was wurde nicht gewählt und warum? (nur wenn bekannt)
   **Folge:** Was ändert sich dadurch? Was ist offen?
   ```
   Datum ist das heutige Datum der Entscheidung. Die Quelle (Pull Request oder Commit) immer angeben.

5. **Offene Punkte pflegen.** Bleibt etwas zu klären, eine Zeile in die Tabelle "Offene Punkte" eintragen. Ist ein
   Punkt erledigt, die Zeile entfernen und im zugehörigen Eintrag den Status nachführen.

6. **Inhaltsverzeichnis und Verweise prüfen.** Die Gruppenlinks oben müssen weiter stimmen. Verweise wie "siehe B5"
   müssen auf einen existierenden Eintrag zeigen.

7. **Zeigen.** `git diff ENTSCHEIDUNGEN.md` ausgeben und kurz zusammenfassen.

## Regeln

- **Nichts erfinden.** Als **Grund** nur eintragen, was der Benutzer gesagt hat oder was Code, Kommentare, Commit- oder
  Pull-Request-Text hergeben. Ist der Grund nicht belegt, schreiben: "Vermutlich … (bitte bestätigen)" oder den
  Benutzer direkt fragen. Das gilt besonders für Entscheidungen, die der Benutzer ohne Claude getroffen hat.
- **Nichts löschen.** Ein überholter Eintrag bleibt stehen und bekommt den Zusatz "Ersetzt durch X1 (Datum)". Der neue
  Eintrag verweist zurück.
- **Fakten prüfen.** Zahlen, Dateinamen und Optionen im Eintrag am Code bestätigen, bevor sie stehen bleiben.
- **Keine Geheimnisse:** keine Passwörter, Tokens oder Serverdaten. Auch nicht in Beispielen oder
  Fehlermeldungen.
- **Sprache:** Deutsch mit Schweizer Schreibweise (`ss` statt `ß`), echte Umlaute.
- **Kurz bleiben:** Ein Eintrag hat fünf bis zehn Zeilen. Details gehören in den Pull Request oder die Doku.
- **Nicht committen oder pushen**, ausser der Benutzer verlangt es ausdrücklich.
