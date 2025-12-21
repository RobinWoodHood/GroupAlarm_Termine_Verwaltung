import io
from pathlib import Path
import pandas as pd
from framework.importers import CSVImporter


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
