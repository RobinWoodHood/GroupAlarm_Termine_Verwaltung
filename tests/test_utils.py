from datetime import datetime, timezone, timedelta
from framework.utils import parse_date, relative_notification


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
