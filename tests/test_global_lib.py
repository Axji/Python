import datetime

from global_lib import GlobalLib


def test_change_positions_swaps_in_place():
    data = [1, 2, 3]
    GlobalLib.change_positions(data, 0, 2)
    assert data == [3, 2, 1]


def test_file_helpers(tmp_path):
    file = tmp_path / "a.txt"
    file.write_text("abc", encoding="utf-8")
    assert GlobalLib.get_file_size(str(file)) == 3
    assert GlobalLib.get_file_path(str(file)) == str(file)


def test_print_empty_lines(capsys):
    GlobalLib.print_empty_lines(2)
    assert capsys.readouterr().out == "\n\n"


def test_iso_dates():
    assert datetime.date.fromisoformat(GlobalLib.date_iso()) == datetime.date.today()
    datetime.datetime.fromisoformat(GlobalLib.date_time_iso())
