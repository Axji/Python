import sqlite3
conn = sqlite3.connect('..\daten\weather.db')

c = conn.cursor()

# Create table

c.execute('drop table weather')
c.execute('''CREATE TABLE weather
            (Station text,
            year number,
            month number,
            temperature real,
            rain real,
            createUser text,
            createTime datetime,
            updateUser text,
            updateTime datetime)''')
conn.commit()
