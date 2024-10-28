import random


class BingoFeld:
    def __init__(self, groesse=5):
        # Erstelle ein leeres Bingo-Feld mit der angegebenen Größe
        self.groesse = groesse
        self.feld = [[None for _ in range(groesse)] for _ in range(groesse)]
        self.feld[groesse // 2][groesse // 2] = 0  # Mitte als freies Feld markieren

    def generiere_feld(self):
        # Fülle das Bingo-Feld mit zufälligen Werten in jeder Spalte
        for spalte in range(self.groesse):
            # Erstellen eines Bereichs von möglichen Werten für jede Spalte
            start = spalte * 15 + 1
            end = start + 15
            werte = random.sample(range(start, end), self.groesse)

            for zeile in range(self.groesse):
                # Überspringe das freie Feld in der Mitte
                if not (spalte == self.groesse // 2 and zeile == self.groesse // 2):
                    self.feld[zeile][spalte] = werte[zeile]

    def zeige_feld(self):
        # Zeige das Bingo-Feld in einer lesbaren Form
        for zeile in self.feld:
            print("\t".join(str(feld) if feld is not None else ' ' for feld in zeile))

    def markiere_zahl(self, zahl):
        # Markiere eine Zahl als 'X', wenn sie auf dem Feld gefunden wird
        for zeile in range(self.groesse):
            for spalte in range(self.groesse):
                if self.feld[zeile][spalte] == zahl:
                    self.feld[zeile][spalte] = self.feld[zeile][spalte] * -1
                    return True
        return False

    def ueberpruefe_bingo(self):
        # Prüfen, ob eine vollständige Zeile, Spalte oder Diagonale markiert ist
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



bingo = BingoFeld()
bingo.generiere_feld()
print("Bingo-Feld:")
bingo.zeige_feld()


# Ziehen und Markieren von Zahlen bis ein Bingo erreicht wird
gezogene_zahlen = list(range(1, 76))  # Alle möglichen Zahlen von 1 bis 75
random.shuffle(gezogene_zahlen)  # Zufällige Reihenfolge der Zahlen

zug_nummer = 0
while not bingo.ueberpruefe_bingo():
    zahl = gezogene_zahlen.pop(0)
    zug_nummer += 1
    print(f"\nZug {zug_nummer}: Ziehe {zahl}")
    bingo.markiere_zahl(zahl)
    bingo.zeige_feld()


