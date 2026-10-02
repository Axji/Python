"""Einfaches neuronales Netz, das ein Auto fährt, plus Speichern/Laden des Gelernten.

Das Netz bekommt die Fühler (Abstand zur Strassenkante in 5 Richtungen) und das Tempo und liefert Lenkung und Gas/Bremse.
Die Gewichte werden nicht per Rückwärtsrechnung, sondern durch Auslese und Mutation gelernt (siehe `train_neural.py`).
"""
import json
import math
import os
import random
import shutil
import time

import constant

HERE = os.path.dirname(os.path.abspath(__file__))
BRAIN_FILE = os.path.join(HERE, "brains", "best_brain.json")

SENSOR_ANGLES = (-60, -30, 0, 30, 60)  # Fühlerrichtungen relativ zur Fahrtrichtung in Grad
SENSOR_RANGE = 150                     # Reichweite der Fühler in Pixeln
LAYERS = (len(SENSOR_ANGLES) + 1, 8, 2)  # Eingänge (Fühler + Tempo), versteckte Neuronen, Ausgänge (Lenkung, Gas)


class NeuralNet:
    """Vorwärtsgerichtetes Netz mit tanh-Neuronen. Alle Gewichte (inkl. Bias) liegen in einer flachen Liste."""

    def __init__(self, weights=None, layers=LAYERS):
        self.layers = tuple(layers)
        count = sum((a + 1) * b for a, b in zip(self.layers, self.layers[1:]))
        self.weights = list(weights) if weights is not None else [random.uniform(-1, 1) for _ in range(count)]
        if len(self.weights) != count:
            raise ValueError(f"Netz {self.layers} braucht {count} Gewichte, bekommen: {len(self.weights)}")

    def forward(self, inputs):
        """Berechnet die Ausgänge (je -1..1) für die Eingänge."""
        values = list(inputs)
        pos = 0
        for size_in, size_out in zip(self.layers, self.layers[1:]):
            out = []
            for _ in range(size_out):
                total = self.weights[pos + size_in]  # Bias
                for k in range(size_in):
                    total += self.weights[pos + k] * values[k]
                pos += size_in + 1
                out.append(math.tanh(total))
            values = out
        return values

    def copy(self):
        return NeuralNet(self.weights, self.layers)

    def mutated(self, rate=0.2, sigma=0.3):
        """Kopie, bei der jedes Gewicht mit Wahrscheinlichkeit `rate` um einen Zufallswert (Streuung `sigma`) abweicht."""
        child = self.copy()
        for i in range(len(child.weights)):
            if random.random() < rate:
                child.weights[i] += random.gauss(0, sigma)
        return child


def save_brain(net, fitness, path=BRAIN_FILE, **info):
    """Speichert das Netz mit Bewertung und Zusatzinfos als JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"layers": list(net.layers), "weights": net.weights, "fitness": fitness, **info}, f, indent=1)


def backup_brain(path=BRAIN_FILE):
    """Kopiert das gespeicherte Netz nach brains/best_brain_JJJJMMTT_HHMMSS.json. Gibt den Pfad zurück oder None."""
    if not os.path.exists(path):
        return None
    base, ext = os.path.splitext(path)
    backup = f"{base}_{time.strftime('%Y%m%d_%H%M%S')}{ext}"
    shutil.copy2(path, backup)
    return backup


def reset_brain(path=BRAIN_FILE):
    """Setzt die KI zurück: sichert das gespeicherte Netz mit Zeitstempel und löscht es dann.

    Danach gibt es kein gespeichertes Netz mehr; das nächste Training beginnt bei null.
    Gibt den Pfad der Sicherung zurück oder None, wenn es nichts zu sichern gab.
    """
    backup = backup_brain(path)
    if backup:
        os.remove(path)
    return backup


def load_brain(path=BRAIN_FILE):
    """Lädt ein gespeichertes Netz. Gibt (Netz, Infos) zurück oder (None, {}), wenn es noch keines gibt."""
    if not os.path.exists(path):
        return None, {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if tuple(data["layers"]) != LAYERS:
        return None, {}  # Netzaufbau hat sich geändert: altes Gelerntes passt nicht mehr
    return NeuralNet(data["weights"], data["layers"]), data


class NeuralDriver:
    """Steuert ein `Car` mit einem `NeuralNet` (wie ein Mensch über `delta_speed` und `delta_view_angle`)."""

    def __init__(self, car, net):
        self.car = car
        self.net = net

    def sensors(self, track_map):
        """Fühlerwerte 0..1 (1 = Strasse bis zur Reichweite frei)."""
        cx = self.car.pos_x + constant.PLAYERWITH / 2
        cy = self.car.pos_y + constant.PLAYERHIGH / 2
        return [track_map.ray(cx, cy, self.car.view_angle + a, SENSOR_RANGE) / SENSOR_RANGE for a in SENSOR_ANGLES]

    def drive(self, track_map):
        """Entscheidet für dieses Bild über Lenkung und Gas/Bremse."""
        rays = self.sensors(track_map)
        if not any(rays):  # keine Strasse in Sicht: anhalten
            self.car.delta_view_angle = 0
            self.car.delta_speed = -constant.ACCELERATIONVALUE if self.car.speed > 0 else 0
            return
        steer, throttle = self.net.forward(rays + [self.car.speed / constant.MAXSPEED])
        self.car.delta_view_angle = steer * constant.STEERINGVALUE
        self.car.delta_speed = throttle * constant.ACCELERATIONVALUE
