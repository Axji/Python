"""Mandelbrot-Generator mit Fenster: zeichnet die Menge in Full-HD und lässt Ausschnitt und Detailgrad einstellen."""
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

# Bildauflösung: Full HD
WIDTH = 1920
HEIGHT = 1080

def escape_iterations(x_min, x_max, y_min, y_max, max_iter):
    """Anzahl Iterationen bis zum Ausbruch je Pixel (max_iter = gehört zur Menge), vektorisiert mit numpy."""
    # Jedem Pixel eine Zahl c der komplexen Ebene zuordnen (x = Realteil, y = Imaginärteil)
    real = np.linspace(x_min, x_max, WIDTH, endpoint=False)
    imag = np.linspace(y_min, y_max, HEIGHT, endpoint=False)
    c = real[np.newaxis, :] + 1j * imag[:, np.newaxis]  # Form (HEIGHT, WIDTH)

    # Iteration z -> z² + c: Bleibt |z| dauerhaft höchstens 2, gehört c zur Mandelbrot-Menge
    z = np.zeros_like(c)
    counts = np.full(c.shape, max_iter, dtype=np.int64)
    active = np.ones(c.shape, dtype=bool)  # Pixel, die noch nicht ausgebrochen sind
    for i in range(max_iter):
        # Nur Pixel weiterrechnen, die noch nicht ausgebrochen sind (spart Rechenzeit)
        z[active] = z[active] ** 2 + c[active]
        escaped = active & (np.abs(z) > 2)
        counts[escaped] = i
        active &= ~escaped
        if not active.any():  # Alle Pixel sind entschieden: vorzeitig beenden
            break
    return counts


def generate_mandelbrot(x_min, x_max, y_min, y_max, max_iter):
    """Erzeugt das Bild: Die Farbe ergibt sich aus der Iterationszahl, die Punkte der Menge selbst sind schwarz."""
    counts = escape_iterations(x_min, x_max, y_min, y_max, max_iter)
    # Drei Farbkanäle aus der Iterationszahl ableiten (mit unterschiedlichen Faktoren, modulo 256)
    rgb = np.stack([counts % 256, (counts * 2) % 256, (counts * 4) % 256], axis=-1).astype(np.uint8)
    rgb[counts == max_iter] = (0, 0, 0)  # Punkte der Menge schwarz
    return Image.fromarray(rgb, 'RGB')

class MandelbrotApp:
    """Fenster mit Eingabefeldern für den Bildausschnitt und die maximale Iterationszahl sowie dem berechneten Bild."""

    def __init__(self, root):
        self.root = root
        self.root.title("Mandelbrot Generator")

        # Standardwerte (zeigt die ganze Menge)
        self.x_min = -2.0
        self.x_max = 1.0
        # y-Bereich passend zum Seitenverhältnis 1920x1080, damit die Pixel quadratisch bleiben
        self.y_min = -0.84375
        self.y_max = 0.84375
        self.max_iter = 100

        # Bedienelemente
        self.frame = ttk.Frame(self.root)
        self.frame.pack(pady=10)

        ttk.Label(self.frame, text="X-Minimum:").grid(row=0, column=0)
        self.x_min_entry = ttk.Entry(self.frame)
        self.x_min_entry.insert(0, str(self.x_min))
        self.x_min_entry.grid(row=0, column=1)

        ttk.Label(self.frame, text="X-Maximum:").grid(row=1, column=0)
        self.x_max_entry = ttk.Entry(self.frame)
        self.x_max_entry.insert(0, str(self.x_max))
        self.x_max_entry.grid(row=1, column=1)

        ttk.Label(self.frame, text="Y-Minimum:").grid(row=2, column=0)
        self.y_min_entry = ttk.Entry(self.frame)
        self.y_min_entry.insert(0, str(self.y_min))
        self.y_min_entry.grid(row=2, column=1)

        ttk.Label(self.frame, text="Y-Maximum:").grid(row=3, column=0)
        self.y_max_entry = ttk.Entry(self.frame)
        self.y_max_entry.insert(0, str(self.y_max))
        self.y_max_entry.grid(row=3, column=1)

        ttk.Label(self.frame, text="Maximale Iterationen:").grid(row=4, column=0)
        self.max_iter_entry = ttk.Entry(self.frame)
        self.max_iter_entry.insert(0, str(self.max_iter))
        self.max_iter_entry.grid(row=4, column=1)

        self.regenerate_button = ttk.Button(self.frame, text="Neu generieren", command=self.regenerate)
        self.regenerate_button.grid(row=5, column=0, columnspan=2, pady=10)

        # Anzeigefläche für das Bild
        self.image_label = ttk.Label(self.root)
        self.image_label.pack()

        # Erstes Bild gleich beim Start berechnen
        self.regenerate()

    def regenerate(self):
        """Liest die Eingaben, berechnet das Bild neu und zeigt es an. Ungültige Eingaben werden ignoriert."""
        try:
            self.x_min = float(self.x_min_entry.get())
            self.x_max = float(self.x_max_entry.get())
            self.y_min = float(self.y_min_entry.get())
            self.y_max = float(self.y_max_entry.get())
            self.max_iter = int(self.max_iter_entry.get())

            img = generate_mandelbrot(self.x_min, self.x_max, self.y_min, self.y_max, self.max_iter)
            self.photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.photo)
        except ValueError:
            pass  # Ungültige Eingabe (keine Zahl): Bild bleibt unverändert

if __name__ == "__main__":
    root = tk.Tk()
    app = MandelbrotApp(root)
    root.mainloop()