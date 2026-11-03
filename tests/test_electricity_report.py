"""Tests für electricity/electricity_report.py: Daten aus der Datenbank lesen und die HTML-Seite erzeugen (ohne Browser)."""
import json
import re
import sqlite3

import pytest

from electricity import electricity_report as er
from electricity import swiss_electricity as se
from tests.test_swiss_electricity import CSV_TEXT


@pytest.fixture
def data_dir(tmp_path):
    """Ordner mit einer Datenbank aus den vier Beispielmonaten."""
    conn = sqlite3.connect(tmp_path / se.DB_NAME)
    se.init_db(conn)
    se.save_to_db(conn, se.parse_csv(CSV_TEXT), '2026-11-03T10:00:00')
    conn.commit()
    conn.close()
    return tmp_path


def test_build_data_has_one_entry_per_month_in_order(data_dir):
    data = er.build_data(str(data_dir / se.DB_NAME))
    assert data['periods'] == ['2000-01', '2000-02', '2025-01', '2026-01']
    assert data['definitiv'] == [1, 1, 1, 0]
    assert data['retrievedAt'] == '2026-11-03T10:00:00'
    assert set(data['series']) == set(er.SERIES)
    assert all(len(values) == 4 for values in data['series'].values())


def test_build_data_keeps_null_and_writes_whole_numbers_as_int(data_dir):
    series = er.build_data(str(data_dir / se.DB_NAME))['series']
    assert series['photovoltaik'] == [None, None, 100, 200]
    assert series['landeserzeugung'][0] == 5487 and isinstance(series['landeserzeugung'][0], int)


def test_build_data_stops_without_database(tmp_path):
    with pytest.raises(SystemExit, match='swiss_electricity.py'):
        er.build_data(str(tmp_path / 'fehlt.db'))


def test_build_data_stops_on_empty_database(tmp_path):
    conn = sqlite3.connect(tmp_path / se.DB_NAME)
    se.init_db(conn)
    conn.close()
    with pytest.raises(SystemExit, match='keine Monatsdaten'):
        er.build_data(str(tmp_path / se.DB_NAME))


def test_build_data_does_not_modify_the_database(data_dir):
    before = (data_dir / se.DB_NAME).read_bytes()
    er.build_data(str(data_dir / se.DB_NAME))
    assert (data_dir / se.DB_NAME).read_bytes() == before


def test_main_writes_page_with_embedded_data(data_dir, capsys):
    er.main(['--daten', str(data_dir)])
    page = (data_dir / er.OUT_NAME).read_text(encoding='utf-8')
    assert '__DATA__' not in page and 'cdn.plot.ly' in page
    embedded = re.search(r'const DATA = (\{.*?\});\nconst MONTHS', page, re.S).group(1)
    assert json.loads(embedded)['periods'][-1] == '2026-01'  # die eingebetteten Daten sind gültiges JSON
    assert 'Fertig:' in capsys.readouterr().out


def test_main_uses_custom_output_file(data_dir):
    out = data_dir / 'unterordner' / 'seite.html'
    er.main(['--daten', str(data_dir), '--out', str(out)])
    assert out.exists()


def test_page_contains_every_chart_container():
    for chart in ['c_surplus', 'c_years', 'c_half', 'c_mix_year']:
        assert f'id="{chart}"' in er.HTML and f"'{chart}'" in er.HTML  # Container vorhanden und von render() befüllt
