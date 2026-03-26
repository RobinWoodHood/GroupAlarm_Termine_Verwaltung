from datetime import datetime, timezone, timedelta

import pytest

from framework.appointment import (
    REMINDER_MAX_MINUTES,
    REMINDER_MIN_MINUTES,
    REMINDER_UNIT_FACTORS,
    convert_reminder_to_minutes,
    validate_reminder_minutes,
)
from framework.utils import (
    parse_date,
    relative_notification,
    format_de_datetime,
    parse_de_datetime,
)


def test_parse_date_with_format_and_tz():
    s = "06.01.2026 19:00"
    dt = parse_date(s, fmt="%d.%m.%Y %H:%M", tz="Europe/Berlin")
    assert dt.year == 2026
    assert dt.hour == 19
    assert dt.tzinfo is not None


def test_parse_date_with_hour_only():
    s = "06.01.2026"
    dt = parse_date(s, fmt="%d.%m.%Y", hour=8, tz="UTC")
    assert dt.hour == 8


def test_relative_notification():
    start = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
    res = relative_notification(start, days_before=5, minutes_before=30)
    assert res == start - timedelta(days=5, minutes=30)


def test_format_de_datetime_converts_utc_to_berlin():
    dt = datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)
    formatted = format_de_datetime(dt)
    assert formatted.text == "15.06.2026 12:00"
    assert formatted.warning is None


def test_format_de_datetime_falls_back_on_invalid_timezone():
    dt = datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)
    formatted = format_de_datetime(dt, tz_name="Mars/Phobos")
    assert formatted.text == dt.isoformat()
    assert formatted.warning is not None


def test_format_de_datetime_handles_dst_transition():
    dt = datetime(2026, 3, 29, 1, 30, tzinfo=timezone.utc)
    formatted = format_de_datetime(dt)
    assert formatted.text == "29.03.2026 03:30"
    assert formatted.warning is None


def test_format_de_datetime_warns_for_naive_datetime_with_bad_timezone():
    dt = datetime(2026, 6, 15, 10, 0)
    formatted = format_de_datetime(dt, tz_name="Invalid/Zone")
    assert formatted.warning is not None
    assert formatted.text.endswith("+00:00")


def test_parse_de_datetime_returns_aware_datetime():
    dt = parse_de_datetime("02.04.2026", "09:30")
    assert dt.tzinfo is not None
    assert dt.hour == 9
    assert dt.minute == 30


def test_reminder_conversion_uses_expected_factors():
    assert REMINDER_UNIT_FACTORS["hours"] == 60
    assert convert_reminder_to_minutes(2, "hours") == 120
    assert convert_reminder_to_minutes(1, "weeks") == 10080


def test_reminder_conversion_rejects_unknown_units():
    with pytest.raises(ValueError):
        convert_reminder_to_minutes(1, "months")


def test_validate_reminder_minutes_guardrail():
    validate_reminder_minutes(REMINDER_MIN_MINUTES)
    validate_reminder_minutes(REMINDER_MAX_MINUTES)
    with pytest.raises(ValueError):
        validate_reminder_minutes(REMINDER_MAX_MINUTES + 1)
