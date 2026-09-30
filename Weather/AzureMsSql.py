import os

import pymssql


def connect():
    """Verbindung zur Azure SQL Datenbank. Zugangsdaten kommen aus Umgebungsvariablen."""
    return pymssql.connect(
        server=os.environ['AZURE_SQL_SERVER'],
        user=os.environ['AZURE_SQL_USER'],
        password=os.environ['AZURE_SQL_PASSWORD'],
        database=os.environ.get('AZURE_SQL_DATABASE', 'AxjiDB1'),
    )
