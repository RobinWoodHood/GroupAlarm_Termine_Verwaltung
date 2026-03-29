import pandas as pd
from framework.mapper import Mapper
from framework.utils import parse_date
from framework.label_mapper import map_labels_from_participants


TEST_TOKEN_MAP = {
    "1.TZ/ZTr TZ": 40436,
    "1.TZ/B": 40427,
    "1.TZ/FGr N": 40433,
    "1.TZ/FGr E": 40429,
    "UFB": [40428, 40431, 40434, 40435],
    "KF CE": 40442,
    "KF BE": 40441,
}


def test_mapper_parses_dates_and_labels():
    # build a pandas Series-like row
    """Test `mapper_parses_dates_and_labels` behavior."""
    data = {
        'Beginn': '06.01.2026 19:00',
        'Ende': '06.01.2026 22:00',
        'Thema': 'Rettungsplattformen',
        'Ort': 'Unterkunft',
        'Dienstart': 'Fachausbildung',
        'Teilnehmer': '1.TZ/B\n1.TZ/FGr N\n1.TZ/ZTr TZ TZ'
    }
    row = pd.Series(data)

    mapping = {
        'name': lambda r, helpers: f"ZTr Ausbildung {r['Thema']}",
        'description': lambda r, helpers: f"Ort: {r.get('Ort')}\nDienstart: {r.get('Dienstart')}\nTeilnehmer: {r.get('Teilnehmer')}",
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: map_labels_from_participants(r.get('Teilnehmer'), TEST_TOKEN_MAP),
        'reminder': 60,
        'notificationDate': {'days_before': 5},
    }

    mapper = Mapper(mapping, defaults={'timezone': 'Europe/Berlin', 'start_hour': 19, 'end_hour': 22})
    appt = mapper.map_row(row)

    assert appt.name.startswith('ZTr Ausbildung')
    assert appt.startDate.hour == 19
    assert appt.endDate.hour == 22
    assert appt.labelIDs == [40427, 40433, 40436]
    payload = appt.to_api_payload()
    assert 'startDate' in payload and 'endDate' in payload
    assert payload['organizationID'] == 13915


def test_name_cleaning_removes_newlines():
    """Test `name_cleaning_removes_newlines` behavior."""
    data = {
        'Beginn': '06.01.2026 19:00',
        'Ende': '06.01.2026 22:00',
        'Thema': 'Rettungsplattformen',
        'Ort': 'Unterkunft',
        'Dienstart': 'S -\nFachausbildung',
        'Teilnehmer': '1.TZ/ZTr TZ TZ'
    }
    row = pd.Series(data)
    mapping = {
        'name': lambda r, helpers: f"{r.get('Dienstart')} - {r.get('Thema')}",
        'description': 'Dienstart',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: map_labels_from_participants(r.get('Teilnehmer'), TEST_TOKEN_MAP),
    }
    mapper = Mapper(mapping, defaults={'timezone': 'Europe/Berlin', 'start_hour': 19, 'end_hour': 22, 'clean_name': True})
    appt = mapper.map_row(row)
    # Name should not contain newline
    assert '\n' not in appt.name
    assert '  ' not in appt.name  # no double spaces

