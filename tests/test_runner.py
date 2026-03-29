import pytest
from framework.runner import Runner
from framework.importers import CSVImporter
from framework.mapper import Mapper
import pandas as pd
from types import SimpleNamespace
from framework.importer_token import ImporterToken


def test_runner_dry_run_does_not_require_token(tmp_path, caplog):
    """Test `runner_dry_run_does_not_require_token` behavior."""
    content = "Beginn;Ende;Thema;Teilnehmer\n06.01.2026 19:00;06.01.2026 22:00;T;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    p.write_text(content, encoding='cp1252')

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='cp1252')
    mapping = {
        'name': 'Thema',
        'description': 'Teilnehmer',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: [40436] if 'ZTr' in (r.get('Teilnehmer') or '') else [],
    }
    runner = Runner(importer, mapping, defaults={'timezone':'Europe/Berlin'}, dry_run=True)
    # should not raise even though no token provided
    runner.run()


def test_runner_non_dry_run_calls_client(monkeypatch, tmp_path):
    # prepare csv
    """Test `runner_non_dry_run_calls_client` behavior."""
    content = "Beginn;Ende;Thema;Teilnehmer\n06.01.2026 19:00;06.01.2026 22:00;T;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    p.write_text(content, encoding='utf-8')

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='utf-8')
    mapping = {
        'name': 'Thema',
        'description': 'Teilnehmer',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: [40436] if 'ZTr' in (r.get('Teilnehmer') or '') else [],
    }

    calls = []

    class FakeClient:
        """Container class `FakeClient`."""
        def __init__(self, token, dry_run=False):
            """Initialize the FakeClient instance."""
            assert token == 'tok'
        def create_appointment(self, appt):
            """Execute `create_appointment`."""
            calls.append(appt)

    monkeypatch.setattr('framework.runner.GroupAlarmClient', FakeClient)

    runner = Runner(importer, mapping, defaults={'timezone':'Europe/Berlin'}, dry_run=False)
    # should raise if no token provided
    with pytest.raises(ValueError):
        runner.run(prompt_token=False, token=None)

    # with token provided it should call create_appointment
    runner.run(prompt_token=False, token='tok')
    assert len(calls) == 1


def test_runner_calls_update_when_id_present(monkeypatch, tmp_path):
    """Test `runner_calls_update_when_id_present` behavior."""
    content = "groupalarm_id;Beginn;Ende;Thema;Teilnehmer\n42;06.01.2026 19:00;06.01.2026 22:00;T;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    p.write_text(content, encoding='utf-8')

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='utf-8')
    mapping = {
        'name': 'Thema',
        'description': 'Teilnehmer',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: [40436] if 'ZTr' in (r.get('Teilnehmer') or '') else [],
    }

    calls = []

    class FakeClient:
        """Container class `FakeClient`."""
        def __init__(self, token, dry_run=False):
            """Initialize the FakeClient instance."""
            assert token == 'tok'
        def update_appointment(self, appt):
            """Execute `update_appointment`."""
            calls.append(appt)

    monkeypatch.setattr('framework.runner.GroupAlarmClient', FakeClient)

    runner = Runner(importer, mapping, defaults={'timezone':'Europe/Berlin'}, dry_run=False, id_column='groupalarm_id')
    runner.run(prompt_token=False, token='tok')
    assert len(calls) == 1
    assert getattr(calls[0], 'id', None) == 42


def test_runner_writes_id_back_on_create(monkeypatch, tmp_path):
    """Test `runner_writes_id_back_on_create` behavior."""
    content = "Beginn;Ende;Thema;Teilnehmer\n06.01.2026 19:00;06.01.2026 22:00;T;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    p.write_text(content, encoding='utf-8')

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='utf-8')
    mapping = {
        'name': 'Thema',
        'description': 'Teilnehmer',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: [40436] if 'ZTr' in (r.get('Teilnehmer') or '') else [],
    }

    class FakeClient:
        """Container class `FakeClient`."""
        def __init__(self, token, dry_run=False):
            """Initialize the FakeClient instance."""
            assert token == 'tok'
        def create_appointment(self, appt):
            """Execute `create_appointment`."""
            return {'id': 321}

    monkeypatch.setattr('framework.runner.GroupAlarmClient', FakeClient)

    runner = Runner(importer, mapping, defaults={'timezone':'Europe/Berlin'}, dry_run=False, id_column='groupalarm_id')
    runner.run(prompt_token=False, token='tok')

    # re-load the csv to check the written id
    import pandas as pd
    df = pd.read_csv(str(p), sep=';', encoding='utf-8')
    assert 'groupalarm_id' in df.columns
    assert int(df.loc[0, 'groupalarm_id']) == 321


def test_runner_writes_id_back_on_update(monkeypatch, tmp_path):
    """Test `runner_writes_id_back_on_update` behavior."""
    content = "groupalarm_id;Beginn;Ende;Thema;Teilnehmer\n42;06.01.2026 19:00;06.01.2026 22:00;T;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    p.write_text(content, encoding='utf-8')

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='utf-8')
    mapping = {
        'name': 'Thema',
        'description': 'Teilnehmer',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: [40436] if 'ZTr' in (r.get('Teilnehmer') or '') else [],
    }

    class FakeClient:
        """Container class `FakeClient`."""
        def __init__(self, token, dry_run=False):
            """Initialize the FakeClient instance."""
            assert token == 'tok'
        def update_appointment(self, appt):
            """Execute `update_appointment`."""
            return {'id': 555}

    monkeypatch.setattr('framework.runner.GroupAlarmClient', FakeClient)

    runner = Runner(importer, mapping, defaults={'timezone':'Europe/Berlin'}, dry_run=False, id_column='groupalarm_id')
    runner.run(prompt_token=False, token='tok')

    # re-load the csv to check the written updated id
    import pandas as pd
    df = pd.read_csv(str(p), sep=';', encoding='utf-8')
    assert 'groupalarm_id' in df.columns
    assert int(df.loc[0, 'groupalarm_id']) == 555


def test_runner_creates_token_on_update_when_missing(monkeypatch, tmp_path):
    # initial csv contains an id but no token; runner should generate a token and persist it
    """Test `runner_creates_token_on_update_when_missing` behavior."""
    content = "groupalarm_id;Beginn;Ende;Thema;Teilnehmer\n42;06.01.2026 19:00;06.01.2026 22:00;T;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    p.write_text(content, encoding='utf-8')

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='utf-8')
    mapping = {
        'name': 'Thema',
        'description': 'Teilnehmer',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: [40436] if 'ZTr' in (r.get('Teilnehmer') or '') else [],
    }

    captured = {}

    class FakeClient:
        """Container class `FakeClient`."""
        def __init__(self, token, dry_run=False):
            """Initialize the FakeClient instance."""
            assert token == 'tok'
        def update_appointment(self, appt):
            """Execute `update_appointment`."""
            captured['desc'] = appt.description
            return {'id': 42}

    monkeypatch.setattr('framework.runner.GroupAlarmClient', FakeClient)

    runner = Runner(importer, mapping, defaults={'timezone':'Europe/Berlin'}, dry_run=False, id_column='groupalarm_id', token_column='ga_importer_token')
    runner.run(prompt_token=False, token='tok')

    import pandas as pd
    df = pd.read_csv(str(p), sep=';', encoding='utf-8')
    assert 'ga_importer_token' in df.columns
    assert df.loc[0, 'ga_importer_token'] is not None
    from framework.importer_token import ImporterToken
    assert ImporterToken.find_in_text(captured['desc']) is not None
    assert ImporterToken.validate_token(df.loc[0, 'ga_importer_token']) is True


def test_runner_writes_token_and_id_on_create(monkeypatch, tmp_path):
    """Test `runner_writes_token_and_id_on_create` behavior."""
    content = "Beginn;Ende;Thema;Teilnehmer\n06.01.2026 19:00;06.01.2026 22:00;T;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    p.write_text(content, encoding='utf-8')

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='utf-8')
    mapping = {
        'name': 'Thema',
        'description': 'Teilnehmer',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: [40436] if 'ZTr' in (r.get('Teilnehmer') or '') else [],
    }

    captured = {}

    class FakeClient:
        """Container class `FakeClient`."""
        def __init__(self, token, dry_run=False):
            """Initialize the FakeClient instance."""
            assert token == 'tok'
        def create_appointment(self, appt):
            # record that description contains token
            """Execute `create_appointment`."""
            captured['desc'] = appt.description
            return {'id': 888}

    monkeypatch.setattr('framework.runner.GroupAlarmClient', FakeClient)

    runner = Runner(importer, mapping, defaults={'timezone':'Europe/Berlin'}, dry_run=False, id_column='groupalarm_id', token_column='ga_importer_token')
    runner.run(prompt_token=False, token='tok')

    import pandas as pd
    df = pd.read_csv(str(p), sep=';', encoding='utf-8')
    assert 'groupalarm_id' in df.columns
    assert 'ga_importer_token' in df.columns
    assert int(df.loc[0, 'groupalarm_id']) == 888
    assert captured['desc'] is not None
    from framework.importer_token import ImporterToken
    assert ImporterToken.find_in_text(captured['desc']) is not None


def test_runner_token_lookup_on_update(monkeypatch, tmp_path):
    # initial csv contains an id and token; but server id changed and update by id will 404
    """Test `runner_token_lookup_on_update` behavior."""
    token = ImporterToken.create_token()
    content = f"groupalarm_id;ga_importer_token;Beginn;Ende;Thema;Teilnehmer\n42;{token};06.01.2026 19:00;06.01.2026 22:00;T;1.TZ/ZTr TZ TZ\n"
    p = tmp_path / "test.csv"
    p.write_text(content, encoding='utf-8')

    importer = CSVImporter(str(p), delimiter=';', date_column='Beginn', encoding='utf-8')
    mapping = {
        'name': 'Thema',
        'description': 'Teilnehmer',
        'startDate': lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'endDate': lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M", tz='Europe/Berlin'),
        'organizationID': 13915,
        'labelIDs': lambda r, helpers: [40436] if 'ZTr' in (r.get('Teilnehmer') or '') else [],
    }

    class FakeClient:
        """Container class `FakeClient`."""
        def __init__(self, token, dry_run=False):
            """Initialize the FakeClient instance."""
            assert token == 'tok'
            self.updated = []
        def update_appointment(self, appt):
            # simulate 404 for original id
            """Execute `update_appointment`."""
            from framework.client import AppointmentNotFound
            if appt.id == 42:
                raise AppointmentNotFound(appt.id)
            self.updated.append(appt)
            return {'id': 999}
        def list_appointments(self, start, end, type_='personal', organization_id=None):
            # return candidate where description contains token and id=999
            """Execute `list_appointments`."""
            return [{'id': 999, 'description': f"something {token} else"}]

    monkeypatch.setattr('framework.runner.GroupAlarmClient', FakeClient)

    runner = Runner(importer, mapping, defaults={'timezone':'Europe/Berlin'}, dry_run=False, id_column='groupalarm_id', token_column='ga_importer_token')
    runner.run(prompt_token=False, token='tok')

    import pandas as pd
    df = pd.read_csv(str(p), sep=';', encoding='utf-8')
    assert int(df.loc[0, 'groupalarm_id']) == 999
