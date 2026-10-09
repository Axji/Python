"""Bingo-Simulation: Ein 5x5-Feld wird erstellt und so lange mit gezogenen Zahlen markiert, bis ein Bingo entsteht."""
import random


class BingoFeld:
    """Ein Bingo-Feld. Zahlen 1-75 verteilt auf 5 Spalten (1-15, 16-30, ...); Mitte ist ein freies Feld."""

    def __init__(self, groesse=5):
        """Erstellt ein leeres Feld mit `groesse` mal `groesse` Feldern."""
        # None = noch leer; die Zahlen trägt erst generiere_feld() ein
        self.groesse = groesse
        self.feld = [[None for _ in range(groesse)] for _ in range(groesse)]
        self.feld[groesse // 2][groesse // 2] = 0  # 0 = freies Feld, zählt in ueberpruefe_bingo() als markiert

    def generiere_feld(self):
        """Füllt das Feld: Jede Spalte erhält zufällige, verschiedene Zahlen aus ihrem eigenen Zahlenbereich."""
        # Klassische Verteilung: Spalte 0 zieht aus 1-15, Spalte 1 aus 16-30 usw.
        for spalte in range(self.groesse):
            # 15 Zahlen pro Spalte; daraus werden `groesse` verschiedene gezogen
            start = spalte * 15 + 1
            end = start + 15
            werte = random.sample(range(start, end), self.groesse)

            for zeile in range(self.groesse):
                # Die Mitte bleibt 0 und wird nicht überschrieben
                if not (spalte == self.groesse // 2 and zeile == self.groesse // 2):
                    self.feld[zeile][spalte] = werte[zeile]

    def zeige_feld(self):
        """Gibt das Feld zeilenweise auf der Konsole aus."""
        # Spalten mit Tab getrennt; freie und markierte Felder siehe _anzeige()
        for zeile in self.feld:
            print("\t".join(self._anzeige(feld) for feld in zeile))

    @staticmethod
    def _anzeige(feld):
        # 0 = freies Feld in der Mitte, negative Zahl = markiert (gezogen)
        if feld is None or feld == 0:
            return ' '
        if feld < 0:
            return 'X'
        return str(feld)

    def markiere_zahl(self, zahl):
        """Markiert die Zahl (durch Vorzeichenwechsel), falls sie auf dem Feld steht. Gibt True zurück, wenn sie gefunden wurde."""
        # Jede Zahl kommt höchstens einmal vor (Spaltenbereiche sind getrennt), nach dem Treffer kann abgebrochen werden
        for zeile in range(self.groesse):
            for spalte in range(self.groesse):
                if self.feld[zeile][spalte] == zahl:
                    self.feld[zeile][spalte] = self.feld[zeile][spalte] * -1
                    return True
        return False

    def ueberpruefe_bingo(self):
        """Gibt True zurück, wenn eine Zeile, Spalte oder Diagonale vollständig markiert ist (markiert = 0 oder negativ)."""
        # `<= 0` statt `< 0`, weil das freie Feld (0) von Anfang an als markiert gilt
        # Zeilen prüfen
        for zeile in self.feld:
            if all(feld <= 0 for feld in zeile):
                return True
        # Spalten prüfen
        for spalte in range(self.groesse):
            if all(self.feld[zeile][spalte] <= 0 for zeile in range(self.groesse)):
                return True
        # Diagonalen prüfen
        if all(self.feld[i][i] <= 0 for i in range(self.groesse)):
            return True
        if all(self.feld[i][self.groesse - 1 - i] <= 0 for i in range(self.groesse)):
            return True
        return False



def spiele():
    """Spielt eine Runde: zieht Zahlen in zufälliger Reihenfolge, bis das Feld ein Bingo hat."""
    bingo = BingoFeld()
    bingo.generiere_feld()
    print("Bingo-Feld:")
    bingo.zeige_feld()

    # Ziehurne: Alle 75 Zahlen einmal mischen und der Reihe nach ziehen, so kommt keine Zahl doppelt dran
    gezogene_zahlen = list(range(1, 76))
    random.shuffle(gezogene_zahlen)

    zug_nummer = 0
    while not bingo.ueberpruefe_bingo():
        zahl = gezogene_zahlen.pop(0)
        zug_nummer += 1
        print(f"\nZug {zug_nummer}: Ziehe {zahl}")
        bingo.markiere_zahl(zahl)
        bingo.zeige_feld()


if __name__ == "__main__":
    spiele()

