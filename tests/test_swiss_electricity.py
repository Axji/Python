"""Tests für electricity/swiss_electricity.py: CSV lesen, Bilanzprüfung, Datenbank und Auswertungs-Sichten (ohne Internet)."""
import datetime
import sqlite3
import urllib.error

import pytest

from electricity import swiss_electricity as se

HEADER = ('Jahr,Monat,Definitiv,Erzeugung_Laufwerk_GWh,Erzeugung_Speicherwerk_GWh,Erzeugung_Kernkraftwerk_GWh,Erzeugung_andere_GWh,'
          'Erzeugung_Thermische_GWh,Erzeugung_Windkraft_GWh,Erzeugung_Photovoltaik_GWh,Landeserzeugung_GWh,Verbrauch_Speicherpumpen_GWh,'
          'Erzeugung_netto_GWh,Einfuhr_GWh,Ausfuhr_GWh,Landesverbrauch_GWh,Verluste_GWh,Endverbrauch_GWh')
# Echte Zeilen aus der Quelle: Januar und Februar 2000 (Überschuss, PV noch NULL), Januar 2025 und 2026 (Unterproduktion, PV vorhanden)
CSV_TEXT = '\n'.join([
    HEADER,
    '2000,1,1,891,2004,2354,238,NULL,NULL,NULL,5487,72,5415,2580,2521,5474,346,5128',
    '2000,2,1,959,1516,2213,232,NULL,NULL,NULL,4920,40,4880,2478,2337,5021,353,4668',
    '2025,1,1,800,2000,1500,NULL,300,10,100,4710,200,4510,3500,1800,6210,400,5810',
    '2026,1,0,704,2177,1454,NULL,363,18,200,4916,301,4615,3686,1909,6392,403,5989',
]) + '\n'


@pytest.fixture
def rows():
    return se.parse_csv(CSV_TEXT)


@pytest.fixture
def conn(rows):
    connection = sqlite3.connect(':memory:')
    se.init_db(connection)
    se.save_to_db(connection, rows, '2026-11-03T10:00:00')
    se.create_views(connection)
    yield connection
    connection.close()


# ---------------------------------------------------------------- CSV lesen


def test_parse_reads_numbers_and_null(rows):
    assert len(rows) == 4
    first = rows[0]
    assert (first['jahr'], first['monat'], first['definitiv']) == (2000, 1, 1)
    assert first['laufwerk_gwh'] == 891 and first['landeserzeugung_gwh'] == 5487
    assert first['photovoltaik_gwh'] is None and first['thermisch_gwh'] is None  # damals nicht ausgewiesen
    assert rows[3]['definitiv'] == 0 and rows[3]['andere_gwh'] is None


def test_parse_rejects_missing_columns():
    with pytest.raises(ValueError, match='Erzeugung_Photovoltaik_GWh'):
        se.parse_csv(CSV_TEXT.replace('Erzeugung_Photovoltaik_GWh', 'Solar'))


def test_parse_rejects_file_without_data():
    with pytest.raises(ValueError):
        se.parse_csv(HEADER + '\n')


def test_parse_accepts_bom_free_text_with_crlf():
    assert len(se.parse_csv(CSV_TEXT.replace('\n', '\r\n'))) == 4


# ---------------------------------------------------------------- Bilanz prüfen


def test_real_rows_are_consistent(rows):
    assert all(se.check_balance(r) == [] for r in rows[:2] + rows[3:])


def test_check_balance_finds_wrong_sum(rows):
    broken = dict(rows[0], landeserzeugung_gwh=5600)
    problems = se.check_balance(broken)
    assert any(p.startswith('Landeserzeugung') for p in problems)


def test_check_balance_allows_rounding_difference(rows):
    assert se.check_balance(dict(rows[0], landeserzeugung_gwh=5489)) == []


def test_check_balance_skips_rules_with_missing_values(rows):
    assert se.check_balance(dict(rows[0], einfuhr_gwh=None, speicherpumpen_gwh=None)) == []


# ---------------------------------------------------------------- Datenbank


def test_save_counts_new_and_changed_rows(rows):
    connection = sqlite3.connect(':memory:')
    se.init_db(connection)
    assert se.save_to_db(connection, rows, 't1') == (4, 0)
    assert se.save_to_db(connection, rows, 't2') == (0, 0)  # gleiche Daten: nichts neu, nichts geändert
    revised = [dict(r) for r in rows]
    revised[3].update(definitiv=1, photovoltaik_gwh=210.0)  # provisorischer Wert wird definitiv und korrigiert
    assert se.save_to_db(connection, revised, 't3') == (0, 1)
    row = connection.execute('SELECT definitiv, photovoltaik_gwh, abgerufen_am FROM monthly WHERE jahr = 2026').fetchone()
    assert row == (1, 210.0, 't3')
    assert connection.execute('SELECT COUNT(*) FROM monthly').fetchone() == (4,)
    connection.close()


def test_null_values_stay_null_in_the_database(conn):
    assert conn.execute('SELECT photovoltaik_gwh FROM monthly WHERE periode = ?', ('2000-01',)).fetchone() == (None,)


def test_log_retrieval(conn, rows):
    se.log_retrieval(conn, 't', 'quelle', rows, 4, 0)
    assert conn.execute('SELECT * FROM abrufe').fetchone() == ('t', 'quelle', 4, '2026-01', 4, 0)


# ---------------------------------------------------------------- Auswertungen


def test_view_monat_surplus_matches_export_minus_import(conn):
    for periode in ('2000-01', '2000-02', '2025-01', '2026-01'):
        surplus, balance = conn.execute('SELECT ueberschuss_gwh, ausfuhr_gwh - einfuhr_gwh FROM v_monat WHERE periode = ?', (periode,)).fetchone()
        assert surplus == pytest.approx(balance, abs=se.TOLERANCE_GWH)
    assert conn.execute('SELECT ueberschuss_gwh FROM v_monat WHERE periode = ?', ('2025-01',)).fetchone() == (-1700,)


def test_view_monat_status_and_self_sufficiency(conn):
    january_2000 = conn.execute('SELECT ueberschuss_gwh, status, eigendeckung_pct FROM v_monat WHERE periode = ?', ('2000-01',)).fetchone()
    assert january_2000[0] == 5415 - 5474 and january_2000[1] == 'Unterproduktion'
    assert january_2000[2] == round(100 * 5415 / 5474, 1)
    # nur ein Monat hat mehr Erzeugung als Verbrauch: ein künstlicher Überschuss
    conn.execute('UPDATE monthly SET erzeugung_netto_gwh = 6000 WHERE periode = ?', ('2000-01',))
    assert conn.execute('SELECT status FROM v_monat WHERE periode = ?', ('2000-01',)).fetchone() == ('Ueberproduktion',)


def test_view_monat_hydro_and_shares(conn):
    row = conn.execute('SELECT wasserkraft_gwh, anteil_wasserkraft_pct, anteil_kernkraft_pct, anteil_photovoltaik_pct '
                       'FROM v_monat WHERE periode = ?', ('2026-01',)).fetchone()
    assert row[0] == 704 + 2177
    assert row[1] == round(100 * 2881 / 4916, 1) and row[2] == round(100 * 1454 / 4916, 1) and row[3] == round(100 * 200 / 4916, 1)
    assert conn.execute('SELECT anteil_photovoltaik_pct FROM v_monat WHERE periode = ?', ('2000-01',)).fetchone() == (None,)


def test_view_jahr_sums_and_completeness(conn):
    year_2000 = conn.execute('SELECT monate, vollstaendig, landeserzeugung_gwh, definitiv FROM v_jahr WHERE jahr = 2000').fetchone()
    assert year_2000 == (2, 0, 5487 + 4920, 1)  # nur zwei Monate: nicht vollständig
    year_2026 = conn.execute('SELECT definitiv, erzeugung_diff_vorjahr_gwh FROM v_jahr WHERE jahr = 2026').fetchone()
    assert year_2026 == (0, 4916 - 4710)  # provisorisch; Differenz zum vorherigen Jahr in den Daten (2025)


def test_view_vorjahr_compares_same_month(conn):
    row = conn.execute('SELECT landeserzeugung_gwh, landeserzeugung_vorjahr_gwh, landeserzeugung_diff_gwh, landeserzeugung_diff_pct '
                       'FROM v_vorjahr WHERE periode = ?', ('2026-01',)).fetchone()
    assert row == (4916, 4710, 206, round(100 * 206 / 4710, 1))
    first = conn.execute('SELECT landeserzeugung_vorjahr_gwh, landeserzeugung_diff_pct FROM v_vorjahr WHERE periode = ?', ('2000-01',)).fetchone()
    assert first == (None, None)  # kein Vorjahr vorhanden


def test_view_halbjahr_labels_winter_across_new_year(conn):
    labels = [r[0] for r in conn.execute('SELECT halbjahr FROM v_halbjahr ORDER BY start_jahr, typ')]
    assert labels == ['Winter 1999/00', 'Winter 2024/25', 'Winter 2025/26']
    winter = conn.execute('SELECT monate, vollstaendig FROM v_halbjahr WHERE halbjahr = ?', ('Winter 1999/00',)).fetchone()
    assert winter == (2, 0)


def test_create_views_can_run_twice(conn):
    se.create_views(conn)
    assert conn.execute('SELECT COUNT(*) FROM v_monat').fetchone() == (4,)


# ---------------------------------------------------------------- Dateien und Ablauf


def test_save_csv_keeps_text_unchanged_and_names_file_by_date(tmp_path):
    path = se.save_csv(CSV_TEXT, str(tmp_path), today=datetime.date(2026, 11, 3))
    assert path.endswith('elektrizitaetsbilanz_monatswerte_20261103.csv')
    with open(path, encoding='utf-8', newline='') as f:
        assert f.read() == CSV_TEXT
    assert se.csv_files(str(tmp_path)) == [path]


def test_run_saves_csv_and_database_and_prints_summary(tmp_path, capsys):
    se.run(str(tmp_path), fetch=lambda: CSV_TEXT)
    output = capsys.readouterr().out
    assert 'Neuester Monat: 2026-01 (provisorisch)' in output and 'Unterproduktion' in output
    assert len(se.csv_files(str(tmp_path))) == 1
    with sqlite3.connect(tmp_path / se.DB_NAME) as db:
        assert db.execute('SELECT COUNT(*) FROM monthly').fetchone() == (4,)
        assert db.execute('SELECT neue_zeilen, geaenderte_zeilen FROM abrufe').fetchone() == (4, 0)


def test_run_offline_reads_the_saved_file(tmp_path, capsys):
    se.run(str(tmp_path), fetch=lambda: CSV_TEXT)
    se.run(str(tmp_path), offline=True, fetch=lambda: pytest.fail('offline darf nichts herunterladen'))
    assert '0 neu, 0 geändert' in capsys.readouterr().out


def test_run_offline_without_file_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        se.run(str(tmp_path), offline=True)


def test_broken_download_does_not_touch_existing_data(tmp_path):
    se.run(str(tmp_path), fetch=lambda: CSV_TEXT)
    with pytest.raises(ValueError):
        se.run(str(tmp_path), fetch=lambda: '<html>Wartungsarbeiten</html>')
    assert len(se.csv_files(str(tmp_path))) == 1
    with sqlite3.connect(tmp_path / se.DB_NAME) as db:
        assert db.execute('SELECT COUNT(*) FROM monthly').fetchone() == (4,)


def test_main_returns_error_code_on_network_failure(tmp_path, monkeypatch, capsys):
    def failing_fetch(url=se.SOURCE_URL):
        raise urllib.error.URLError('kein Netz')

    monkeypatch.setattr(se, 'fetch_csv', failing_fetch)
    assert se.main(['--daten', str(tmp_path)]) == 1
    assert 'Fehler' in capsys.readouterr().err


def test_fetch_retries_and_then_gives_up(monkeypatch):
    calls = []

    def failing_urlopen(*args, **kwargs):
        calls.append(1)
        raise urllib.error.URLError('Abbruch')

    monkeypatch.setattr(se.urllib.request, 'urlopen', failing_urlopen)
    monkeypatch.setattr(se.time, 'sleep', lambda seconds: None)
    with pytest.raises(urllib.error.URLError):
        se.fetch_csv('https://example.invalid/x.csv')
    assert len(calls) == se.REQUEST_ATTEMPTS
