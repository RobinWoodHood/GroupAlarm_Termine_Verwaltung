"""Tests for Appointment dataclass — recurrence field."""
from datetime import datetime, timezone
from framework.appointment import Appointment


def _make_appt(**kwargs):
    """Internal helper for `make_appt`."""
    defaults = dict(
        name="Test",
        description="desc",
        startDate=datetime(2026, 1, 6, 19, 0, tzinfo=timezone.utc),
        endDate=datetime(2026, 1, 6, 22, 0, tzinfo=timezone.utc),
        organizationID=100,
    )
    defaults.update(kwargs)
    return Appointment(**defaults)


def test_recurrence_defaults_to_none():
    """Test `recurrence_defaults_to_none` behavior."""
    appt = _make_appt()
    assert appt.recurrence is None


def test_recurrence_populated_from_dict():
    """Test `recurrence_populated_from_dict` behavior."""
    rec = {"frequency": "weekly", "interval": 2, "days": [1, 3]}
    appt = _make_appt(recurrence=rec)
    assert appt.recurrence == rec
    assert appt.recurrence["frequency"] == "weekly"


def test_recurrence_not_in_api_payload():
    """Test `recurrence_not_in_api_payload` behavior."""
    rec = {"frequency": "daily", "interval": 1}
    appt = _make_appt(recurrence=rec)
    payload = appt.to_api_payload()
    assert "recurrence" not in payload


def test_recurrence_none_not_in_payload():
    """Test `recurrence_none_not_in_payload` behavior."""
    appt = _make_appt()
    payload = appt.to_api_payload()
    assert "recurrence" not in payload
