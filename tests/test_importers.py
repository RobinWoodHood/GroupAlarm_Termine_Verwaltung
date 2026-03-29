import io
from pathlib import Path
import pandas as pd
from framework.importers import CSVImporter, ExcelImporter


def test_csv_importer_reads_cp1252(tmp_path):
    content = "Tag;Beginn;Ende;Thema;Teilnehmer\nDie;06.01.2026 19:00;10.03.2026 23:00;Test;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    # write in cp1252 encoding to simulate Excel/Windows output
    p.write_bytes(content.encode('cp1252'))

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='cp1252')
    rows = list(importer.rows())
    assert len(rows) == 1
    row = rows[0]
    assert row['Beginn'] == '06.01.2026 19:00'
    assert 'ZTr' in row['Teilnehmer']


def test_excel_importer_none_sheet_reads_first_sheet(monkeypatch):
    calls: dict[str, object] = {}
    df = pd.DataFrame([{"name": "A"}])

    def _fake_read_excel(filename, sheet_name=0, header=0):
        calls["sheet_name"] = sheet_name
        return df

    monkeypatch.setattr("framework.importers.pd.read_excel", _fake_read_excel)

    importer = ExcelImporter("dummy.xlsx", sheet_name=None)
    rows = list(importer.rows())

    assert calls["sheet_name"] == 0
    assert len(rows) == 1
