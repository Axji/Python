"""Simulation einer 10x10-Matrix: Jede Zelle zählt in einem eigenen Thread und in eigenem Tempo von 0 bis 9 hoch.

Das Fenster (tkinter) zeigt die Matrix, die Anzahl Aktualisierungen und die verstrichene Zeit. Start, Stop und Reset
steuern die Simulation.
"""
import random
import threading
import time
import tkinter as tk

SIZE = 10          # Kantenlänge der Matrix
REFRESH_MS = 100   # Abstand zwischen zwei Bildschirmaktualisierungen in Millisekunden

# Zustand: Die Worker-Threads ändern nur diese Daten (unter Lock).
# Alle Tk-Widgets werden ausschliesslich im Hauptthread über root.after aktualisiert,
# denn Tk ist nicht thread-sicher.
lock = threading.Lock()
matrix = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
speed_matrix = [[0 for _ in range(SIZE)] for _ in range(SIZE)]  # Tempo je Zelle, einmal pro Start festgelegt
update_counter = 0  # Anzahl aller Zellenänderungen seit dem Start
start_time = None   # Startzeitpunkt für die Zeitanzeige
stop_event = None  # None = nicht gestartet; sonst das Event der laufenden Simulation


def increment_cell(row, col, stop):
    """Zählt eine Zelle im eigenen Tempo hoch (9 -> 0), bis die Simulation gestoppt wird."""
    global update_counter
    speed = speed_matrix[row][col]
    while not stop.wait(speed):  # wait() kehrt sofort zurück, sobald gestoppt wird
        with lock:
            matrix[row][col] = (matrix[row][col] + 1) % 10
            update_counter += 1


def is_running():
    """Gibt True zurück, wenn eine Simulation gestartet und noch nicht gestoppt wurde."""
    return stop_event is not None and not stop_event.is_set()


def display_matrix():
    """Zeigt den aktuellen Zustand im Fenster an (nur im Hauptthread aufrufen)."""
    with lock:
        lines = [" ".join(str(x) for x in row) for row in matrix]
        counter = update_counter
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, "\n".join(lines) + "\n")
    text_widget.config(state=tk.DISABLED)
    counter_label.config(text=f"Updates: {counter}")
    if start_time is not None:
        timer_label.config(text=f"Elapsed: {time.time() - start_time:.1f}s")


def refresh():
    """Aktualisiert die Anzeige und plant sich selbst erneut ein, solange die Simulation läuft."""
    display_matrix()
    if is_running():
        root.after(REFRESH_MS, refresh)


def start_simulation():
    """Startet die Simulation: würfelt pro Zelle ein Tempo und startet für jede Zelle einen Thread."""
    global stop_event, start_time
    if is_running():
        return
    start_time = time.time()
    for i in range(SIZE):
        for j in range(SIZE):
            speed_matrix[i][j] = random.uniform(0.2, 2.0)
    stop_event = threading.Event()
    for i in range(SIZE):
        for j in range(SIZE):
            threading.Thread(target=increment_cell, args=(i, j, stop_event), daemon=True).start()
    refresh()


def stop_simulation():
    """Stoppt alle Threads (über das Stop-Signal) und zeigt den letzten Stand an."""
    if stop_event is not None:
        stop_event.set()
    display_matrix()


def reset_simulation():
    """Stoppt die Simulation und setzt Matrix, Zähler und Zeit auf 0 zurück."""
    global update_counter, start_time
    stop_simulation()
    with lock:
        update_counter = 0
        for i in range(SIZE):
            for j in range(SIZE):
                matrix[i][j] = 0
    start_time = None
    timer_label.config(text="Elapsed: 0.0s")
    display_matrix()


if __name__ == "__main__":
    # Fenster mit Schaltflächen, Anzeigen und Textfeld für die Matrix aufbauen
    root = tk.Tk()
    root.title("Matrix Display")
    root.geometry("500x500")

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Start", command=start_simulation).grid(row=0, column=0, padx=5)
    tk.Button(button_frame, text="Stop", command=stop_simulation).grid(row=0, column=1, padx=5)
    tk.Button(button_frame, text="Reset", command=reset_simulation).grid(row=0, column=2, padx=5)

    counter_label = tk.Label(root, text="Updates: 0", font=("Courier", 10))
    counter_label.pack(pady=5)

    timer_label = tk.Label(root, text="Elapsed: 0.0s", font=("Courier", 10))
    timer_label.pack(pady=5)

    text_widget = tk.Text(root, font=("Courier", 12), state=tk.DISABLED)
    text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    root.mainloop()
    # Nach dem Schliessen des Fensters laufende Threads beenden
    if stop_event is not None:
        stop_event.set()
    print("Done!")
