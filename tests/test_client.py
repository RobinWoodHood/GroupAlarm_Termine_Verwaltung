import types
import pytest
from framework.client import GroupAlarmClient
from framework.appointment import Appointment
from datetime import datetime, timezone


def make_appt():
    return Appointment(
        name='foo',
        description='desc',
        startDate=datetime(2026,1,6,19,0,tzinfo=timezone.utc),
        endDate=datetime(2026,1,6,22,0,tzinfo=timezone.utc),
        organizationID=13915,
        labelIDs=[40436]
    )


def test_create_appointment_dry_run_no_token():
    client = GroupAlarmClient(token=None, dry_run=True)
    appt = make_appt()
    res = client.create_appointment(appt)
    assert res.get('dry_run') is True
    assert 'payload' in res


def test_create_appointment_requires_token_when_not_dry():
    client = GroupAlarmClient(token=None, dry_run=False)
    appt = make_appt()
    with pytest.raises(ValueError):
        client.create_appointment(appt)


def test_create_appointment_posts(monkeypatch):
    client = GroupAlarmClient(token='sekret', dry_run=False)
    appt = make_appt()

    class DummyResp:
        status_code = 201
        def json(self):
            return {'id': 123}

    def fake_post(url, json, headers, timeout):
        assert headers.get('Personal-Access-Token') == 'sekret'
        return DummyResp()

    monkeypatch.setattr('framework.client.requests.post', fake_post)
    res = client.create_appointment(appt)
    assert res == {'id': 123}


def test_update_appointment_dry_run_no_token():
    client = GroupAlarmClient(token=None, dry_run=True)
    appt = make_appt()
    appt.id = 5
    res = client.update_appointment(appt)
    assert res.get('dry_run') is True
    assert res.get('id') == 5


def test_update_appointment_requires_token_when_not_dry():
    client = GroupAlarmClient(token=None, dry_run=False)
    appt = make_appt()
    appt.id = 7
    with pytest.raises(ValueError):
        client.update_appointment(appt)


def test_update_appointment_puts(monkeypatch):
    client = GroupAlarmClient(token='sekret', dry_run=False)
    appt = make_appt()
    appt.id = 99

    class DummyResp:
        status_code = 200
        def json(self):
            return {'id': 99}

    def fake_put(url, json, headers, timeout):
        assert headers.get('Personal-Access-Token') == 'sekret'
        assert url.endswith('/appointment/99')
        # API requires the id also to be present in the body and to match the path
        assert json.get('id') == 99
        return DummyResp()

    monkeypatch.setattr('framework.client.requests.put', fake_put)
    res = client.update_appointment(appt)
    assert res == {'id': 99}


def test_get_appointment_dry_run_no_token():
    client = GroupAlarmClient(token=None, dry_run=True)
    res = client.get_appointment(10)
    assert res.get('dry_run') is True
    assert res.get('id') == 10


def test_get_appointment_not_found_raises(monkeypatch):
    from framework.client import AppointmentNotFound
    client = GroupAlarmClient(token='sekret', dry_run=False)

    class DummyResp:
        status_code = 404
        text = '{"success":false,"message":"Eintrag nicht gefunden"}'

    def fake_get(url, headers, timeout):
        return DummyResp()

    monkeypatch.setattr('framework.client.requests.get', fake_get)

    with pytest.raises(AppointmentNotFound):
        client.get_appointment(13)


def test_update_appointment_raises_not_found(monkeypatch):
    from framework.client import AppointmentNotFound
    client = GroupAlarmClient(token='sekret', dry_run=False)
    appt = make_appt()
    appt.id = 77

    class DummyResp:
        status_code = 404
        text = '{"success":false,"message":"Eintrag nicht gefunden"}'

    def fake_put(url, json, headers, timeout):
        return DummyResp()

    monkeypatch.setattr('framework.client.requests.put', fake_put)

    with pytest.raises(AppointmentNotFound):
        client.update_appointment(appt)


def test_get_appointment_returns_json(monkeypatch):
    client = GroupAlarmClient(token='sekret', dry_run=False)

    class DummyResp:
        status_code = 200
        def json(self):
            return {'id': 42, 'name': 'foo'}
        def raise_for_status(self):
            return None

    def fake_get(url, headers, timeout):
        return DummyResp()

    monkeypatch.setattr('framework.client.requests.get', fake_get)
    res = client.get_appointment(42)
    assert res == {'id': 42, 'name': 'foo'}
