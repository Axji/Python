"""Startet das Jump-and-Run.

Aufruf (von überall):
    python jumprun1/main.py

Steuerung:
    Pfeil links/rechts oder A/D   laufen
    Leertaste, Pfeil hoch oder W   springen (länger drücken = höher)
    X, J oder Strg                 schiessen, geradeaus nach vorne (gedrückt halten = Dauerfeuer)
    R                              nach Spielende von vorne beginnen
    Esc                            beenden

Ziel: bis zur Fahne am Ende kommen. Gegner lassen sich abschiessen oder von oben anspringen.
"""
import os
import sys

# Das Paket `jumprun1` liegt eine Ebene höher; damit der Start auch aus dem Ordner selbst klappt, wird dieser Pfad ergänzt.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jumprun1.game import Game  # noqa: E402


def main():
    Game().run()


if __name__ == "__main__":
    main()
