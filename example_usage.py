"""Example usage of the new framework.

This example reads `Test.csv` (semicolon-delimited), parses German date format "06.01.2026 19:00",
maps participant codes and sets label 40436 when a 'ZTr' token is present.

Run this file and follow the prompt for your token. Set `dry_run=True` to preview payloads.
"""
from typing import Dict, Iterable

from framework import configure_logging
from framework.importers import CSVImporter
from framework.label_mapper import map_labels_from_participants
from framework.runner import Runner
from framework.utils import parse_date

# Configure logs: print to terminal and write to rotating file 'groupalarm.log'
configure_logging(level='INFO', logfile='groupalarm.log', max_bytes=5 * 1024 * 1024, backup_count=5)


LabelValue = int | Iterable[int]

DEFAULT_TOKEN_MAP: Dict[str, LabelValue] = {
    "1.TZ/ZTr TZ": 40436,
    "1.TZ/B": 40427,
    "1.TZ/FGr N": 40433,
    "1.TZ/FGr E": 40429,
    "UFB": [40428, 40431, 40434, 40435],
    "KF CE": 40442,
    "KF BE": 40441,
}

# You can extend DEFAULT_TOKEN_MAP or pass your own map to `map_labels_from_participants`.
# DEFAULT_TOKEN_MAP currently contains: ZTr, FGr, N, E


mapping = {
    "name": lambda r, helpers: f"{r['Dienstart']}",
    "description": lambda r, helpers: f"Ort: {r.get('Ort')}\nThema: {r.get('Thema')}\nTeilnehmer: {r.get('Teilnehmer')}\nBekleidung: {r.get('Bekleidung')}",
    # parse German datetime format from 'Beginn' and 'Ende' columns
    "startDate": lambda r, helpers: helpers["parse_date"](r["Beginn"], fmt="%d.%m.%Y %H:%M:%S", tz="Europe/Berlin"),
    "endDate": lambda r, helpers: helpers["parse_date"](r["Ende"], fmt="%d.%m.%Y %H:%M:%S", tz="Europe/Berlin"),
    "organizationID": 13915,
    # dynamic label mapping based on Teilnehmer column
    "labelIDs": lambda r, helpers: map_labels_from_participants(r.get('Teilnehmer'), DEFAULT_TOKEN_MAP),
    # reminder can be fixed or from a column; here fixed 60 minutes
    "reminder": 60*24, # minutes
    # notification: 5 days before start
    "notificationDate": {"days_before": 5},
    "isPublic": False,
}


if __name__ == "__main__":
    # Many Windows/Excel-generated CSVs use cp1252 (Windows-1252). If you still see decode errors,
    # set encoding to 'utf-8-sig' or 'utf-16' depending on source.
    # importer = CSVImporter("Z:\\01-Ausbildung\\2026\\Dienst- _ Ausbildungsplan_gesamt.csv", delimiter=';', date_column="Beginn", encoding='cp1252')
    importer = CSVImporter("Z:\\01-Ausbildung\\2026\\Dienst- _ Ausbildungsplan_E.csv", delimiter=';', date_column="Beginn", encoding='cp1252')
    runner = Runner(importer, mapping, defaults={"timezone": "Europe/Berlin", "start_hour": 19, "end_hour": 22}, dry_run=False)
    runner.run()
