import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

# Full HD resolution
WIDTH = 1920
HEIGHT = 1080

def escape_iterations(x_min, x_max, y_min, y_max, max_iter):
    """Anzahl Iterationen bis zum Ausbruch je Pixel (max_iter = gehört zur Menge), vektorisiert mit numpy."""
    real = np.linspace(x_min, x_max, WIDTH, endpoint=False)
    imag = np.linspace(y_min, y_max, HEIGHT, endpoint=False)
    c = real[np.newaxis, :] + 1j * imag[:, np.newaxis]  # Form (HEIGHT, WIDTH)

    z = np.zeros_like(c)
    counts = np.full(c.shape, max_iter, dtype=np.int64)
    active = np.ones(c.shape, dtype=bool)  # Pixel, die noch nicht ausgebrochen sind
    for i in range(max_iter):
        z[active] = z[active] ** 2 + c[active]
        escaped = active & (np.abs(z) > 2)
        counts[escaped] = i
        active &= ~escaped
        if not active.any():
            break
    return counts


def generate_mandelbrot(x_min, x_max, y_min, y_max, max_iter):
    counts = escape_iterations(x_min, x_max, y_min, y_max, max_iter)
    rgb = np.stack([counts % 256, (counts * 2) % 256, (counts * 4) % 256], axis=-1).astype(np.uint8)
    rgb[counts == max_iter] = (0, 0, 0)  # Punkte der Menge schwarz
    return Image.fromarray(rgb, 'RGB')

class MandelbrotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mandelbrot Generator")

        # Default parameters
        self.x_min = -2.0
        self.x_max = 1.0
        # y-Bereich passend zum Seitenverhältnis 1920x1080, damit die Pixel quadratisch bleiben
        self.y_min = -0.84375
        self.y_max = 0.84375
        self.max_iter = 100

        # GUI elements
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

        # Image display
        self.image_label = ttk.Label(self.root)
        self.image_label.pack()

        # Initial generation
        self.regenerate()

    def regenerate(self):
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
            pass  # Ignore invalid input

if __name__ == "__main__":
    root = tk.Tk()
    app = MandelbrotApp(root)
    root.mainloop()