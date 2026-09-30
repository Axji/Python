"""Verbindung zur Azure-SQL-Datenbank.

Benötigte Umgebungsvariablen: AZURE_SQL_SERVER, AZURE_SQL_USER, AZURE_SQL_PASSWORD
(optional AZURE_SQL_DATABASE, sonst 'AxjiDB1'). Zugangsdaten werden nie im Code abgelegt.
"""
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
