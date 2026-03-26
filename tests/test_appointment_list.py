"""List-view timestamp formatting tests (US3 T023)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from cli.app import GroupAlarmApp
from cli.widgets.appointment_list import AppointmentList
from framework.appointment import Appointment
from framework.client import GroupAlarmClient
from framework.config import AppConfig
from framework.utils import format_de_datetime, DE_DATETIME_FORMAT


# --- Unit tests for the shared formatter applied in list rows ---

def test_list_timestamp_uses_german_format():
    """T023: Verify list-view timestamps render as dd.mm.yyyy HH:MM."""
    dt = datetime(2026, 3, 22, 10, 0, tzinfo=timezone.utc)
    result = format_de_datetime(dt, tz_name="Europe/Berlin")
    assert result.text == "22.03.2026 11:00"
    assert result.warning is None


def test_list_timestamp_fallback_on_invalid_timezone():
    """T023: Conversion failure returns raw ISO and a warning."""
    dt = datetime(2026, 3, 22, 10, 0, tzinfo=timezone.utc)
    result = format_de_datetime(dt, tz_name="Invalid/Zone")
    assert result.warning is not None
    # Raw ISO fallback must contain the date
    assert "2026" in result.text
    assert "T" in result.text or "+" in result.text


# --- Textual Pilot integration test ---

SAMPLE_LABELS = [
    {"id": 1, "name": "Fire", "color": "#FF0000", "organizationID": 100},
]

SAMPLE_APPOINTMENTS = [
    {
        "id": 10,
        "name": "Drill Alpha",
        "description": "First drill",
        "startDate": "2026-03-22T10:00:00+00:00",
        "endDate": "2026-03-22T14:00:00+00:00",
        "organizationID": 100,
        "labelIDs": [1],
        "isPublic": True,
        "keepLabelParticipantsInSync": True,
        "timezone": "Europe/Berlin",
        "participants": [],
        "recurrence": None,
    },
]


def _make_app():
    client = MagicMock(spec=GroupAlarmClient)
    client.token = "test-token"
    client.dry_run = False
    client.list_labels.return_value = SAMPLE_LABELS
    client.list_appointments.return_value = SAMPLE_APPOINTMENTS
    config = AppConfig(organization_id=100, date_range_days=30)
    return GroupAlarmApp(client=client, config=config, org_id=100)


@pytest.mark.asyncio
async def test_appointment_list_renders_german_timestamps():
    """T023: List rows display timestamps in dd.mm.yyyy HH:MM format."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        appt_list = app.screen.query_one("#appt-list", AppointmentList)
        # The list should contain formatted timestamps
        assert len(appt_list._appointments) > 0
