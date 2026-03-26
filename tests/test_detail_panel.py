"""Unit tests for EditFormState, detail-panel formatting, and spacing (US2 T016 / US3 T024)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from framework.appointment import Appointment
from framework.utils import format_de_datetime
from cli.widgets.detail_panel import EditFormState


def _sample_appointment() -> Appointment:
    start = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
    return Appointment(
        id=77,
        name="Winter Exercise",
        description="Quarterly drill",
        startDate=start,
        endDate=start + timedelta(hours=2),
        organizationID=100,
        labelIDs=[1, 2],
        timezone="UTC",
        notificationDate=start - timedelta(hours=4),
    )


def test_edit_form_state_formats_datetimes_in_german_locale():
    """T016: Ensure EditFormState splits German-formatted timestamps."""
    state = EditFormState.from_appointment(_sample_appointment(), display_timezone="Europe/Berlin")

    assert state.start_date == "15.01.2026"
    assert state.start_time == "11:00"
    assert state.end_date == "15.01.2026"
    assert state.end_time == "13:00"
    assert state.notification_date == "15.01.2026"
    assert state.notification_time == "07:00"
    assert state.conversion_warnings == []


def test_edit_form_state_validates_temporal_ordering():
    """T016: Validate start/end ordering and notification timing."""
    state = EditFormState.from_appointment(_sample_appointment(), display_timezone="Europe/Berlin")
    state.end_date = "14.01.2026"
    state.end_time = "10:30"
    state.notification_date = "16.01.2026"
    state.notification_time = "08:00"

    errors = state.validate_temporal_ordering()
    assert any("Ende" in message for message in errors)
    assert any("Benachrichtigung" in message for message in errors)


def test_edit_form_state_reminder_conversion_guardrail():
    """T016: Reminder conversion enforces API guardrails."""
    state = EditFormState.from_appointment(_sample_appointment())

    state.apply_reminder("2", "hours")
    assert state.reminder.minutes_total == 120
    assert state.reminder.warning is None

    state.apply_reminder(8, "weeks")
    assert state.reminder.minutes_total is None
    assert "10080" in state.reminder.warning


# --- T024: Detail-panel formatting and optional-field rendering ---


def _appt_with_optional_fields() -> Appointment:
    """Appointment with all optional fields populated."""
    start = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)
    return Appointment(
        id=99,
        name="Summer Drill",
        description="Full-scale exercise",
        startDate=start,
        endDate=start + timedelta(hours=3),
        organizationID=100,
        labelIDs=[1],
        timezone="UTC",
        reminder=120,
        notificationDate=start - timedelta(hours=2),
        feedbackDeadline=start + timedelta(days=1),
    )


def _appt_without_optional_fields() -> Appointment:
    """Appointment with no optional fields."""
    start = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)
    return Appointment(
        id=88,
        name="Basic Meeting",
        description="",
        startDate=start,
        endDate=start + timedelta(hours=1),
        organizationID=100,
        timezone="UTC",
    )


def test_detail_timestamps_format_in_german():
    """T024: All date/time fields display as dd.mm.yyyy HH:MM."""
    state = EditFormState.from_appointment(
        _appt_with_optional_fields(), display_timezone="Europe/Berlin"
    )
    # Summer time: UTC+2
    assert state.start_date == "15.06.2026"
    assert state.start_time == "16:00"
    assert state.end_date == "15.06.2026"
    assert state.end_time == "19:00"
    assert state.notification_date == "15.06.2026"
    assert state.notification_time == "14:00"
    assert state.conversion_warnings == []


def test_detail_optional_fields_absent_renders_empty():
    """T024: Missing optional fields produce empty strings, not errors."""
    state = EditFormState.from_appointment(
        _appt_without_optional_fields(), display_timezone="Europe/Berlin"
    )
    assert state.notification_date == ""
    assert state.notification_time == ""
    assert state.reminder.value is None
    assert state.reminder.minutes_total is None
    assert state.conversion_warnings == []


def test_detail_conversion_failure_produces_warning():
    """T024: Invalid timezone falls back to raw ISO + warning."""
    appt = _appt_with_optional_fields()
    state = EditFormState.from_appointment(appt, display_timezone="Bad/Zone")
    assert len(state.conversion_warnings) > 0
    # Fallback text should contain the raw ISO date portion
    assert "2026" in state.start_date
