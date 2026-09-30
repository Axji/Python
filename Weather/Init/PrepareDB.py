import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'daten', 'weather.db')

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)

c = conn.cursor()

# Create table (bestehende Daten bleiben erhalten)
c.execute('''CREATE TABLE IF NOT EXISTS weather
            (Station text,
            year integer,
            month integer,
            temperature real,
            rain real,
            createUser text,
            createTime datetime,
            updateUser text,
            updateTime datetime)''')
conn.commit()
conn.close()
