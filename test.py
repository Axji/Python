import random
import time
import threading
import tkinter as tk

# Create a 10x10 matrix
matrix = [[0 for _ in range(10)] for _ in range(10)]

# Create a 10x10 speed matrix (speed determined once per cell)
speed_matrix = [[0 for _ in range(10)] for _ in range(10)]
running = False
threads = []

# Create root window
root = tk.Tk()
root.title("Matrix Display")
root.geometry("500x500")

# Create frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

start_button = tk.Button(button_frame, text="Start", command=lambda: start_simulation())
start_button.grid(row=0, column=0, padx=5)

stop_button = tk.Button(button_frame, text="Stop", command=lambda: stop_simulation())
stop_button.grid(row=0, column=1, padx=5)

reset_button = tk.Button(button_frame, text="Reset", command=lambda: reset_simulation())
reset_button.grid(row=0, column=2, padx=5)

# Create label for update counter
counter_label = tk.Label(root, text="Updates: 0", font=("Courier", 10))
counter_label.pack(pady=5)

# Timer label
start_time = None

timer_label = tk.Label(root, text="Elapsed: 0.0s", font=("Courier", 10))
timer_label.pack(pady=5)

# Create text widget to display matrix
text_widget = tk.Text(root, font=("Courier", 12), state=tk.DISABLED)
text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Update counter
update_counter = 0

def increment_cell(row, col):
    """Increment a cell value with assigned speed"""
    global update_counter, running
    speed = speed_matrix[row][col]  # Use predefined speed for this cell
    while matrix[row][col] < 10 and running:
        time.sleep(speed)
        if running:  # Double-check before incrementing
            matrix[row][col] += 1
            if matrix[row][col] == 10:
                matrix[row][col] = 0
            update_counter += 1
            # Update display every 10 changes
            if update_counter % 10 == 0:
                display_matrix()

def display_matrix():
    """Display the current matrix state in the window"""
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    for row in matrix:
        text_widget.insert(tk.END, " ".join(str(x) for x in row) + "\n")
    text_widget.config(state=tk.DISABLED)
    counter_label.config(text=f"Updates: {update_counter}")
    # update timer label
    if start_time is not None:
        elapsed = time.time() - start_time
        timer_label.config(text=f"Elapsed: {elapsed:.1f}s")
    root.update()

def start_simulation():
    """Start the simulation"""
    global running, threads, update_counter, start_time
    if not running:
        running = True
        # update_counter = 0
        start_time = time.time()
        threads = []
        # Initialize speed for each cell (only once)
        for i in range(10):
            for j in range(10):
                speed_matrix[i][j] = random.uniform(0.2, 2.0)
        # Start threads
        for i in range(10):
            for j in range(10):
                thread = threading.Thread(target=increment_cell, args=(i, j))
                thread.daemon = True
                thread.start()
                threads.append(thread)
        display_matrix()

def stop_simulation():
    """Stop the simulation"""
    global running
    running = False

def reset_simulation():
    """Reset the matrix"""
    global running, update_counter, start_time
    running = False
    update_counter = 0
    start_time = None
    timer_label.config(text="Elapsed: 0.0s")
    # Reset matrix values
    for i in range(10):
        for j in range(10):
            matrix[i][j] = 0
    display_matrix()

# Run the tkinter event loop
root.mainloop()

print("Done!")