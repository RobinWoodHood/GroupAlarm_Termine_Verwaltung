from __future__ import annotations
from datetime import datetime, time, timedelta, timezone
from typing import NamedTuple, Optional

from dateutil import parser as dateutil_parser

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - fallback only used on older platforms
    ZoneInfo = None

DE_DATETIME_FORMAT = "%d.%m.%Y %H:%M"
DEFAULT_DISPLAY_TZ = "Europe/Berlin"


class DisplayFormatResult(NamedTuple):
    """Result returned by :func:`format_de_datetime` including warning metadata."""

    text: str
    warning: Optional[str] = None


def parse_date(value, hour: Optional[int] = None, tz: str = "UTC", fmt: Optional[str] = None) -> datetime:
    """Parse a value into a timezone-aware :class:`datetime.datetime`.

    Parameters
    ----------
    value : str or datetime-like
        Input value to parse. May be a :class:`str`, :class:`pandas.Timestamp`, :class:`datetime.datetime` or date-like object.
    hour : int, optional
        If provided and the parsed value has no time component, set the hour to this value (minutes default to zero).
    tz : str, optional
        IANA timezone string to attach to the resulting datetime (default: ``"UTC"``).
    fmt : str, optional
        Explicit :func:`datetime.strptime` format string (e.g. ``"%d.%m.%Y %H:%M"``). If provided an initial ``strptime`` attempt will be made and on failure the function falls back to ``dateutil.parser.parse`` for greater robustness.

    Returns
    -------
    datetime
        A timezone-aware :class:`datetime.datetime` instance.

    Raises
    ------
    ValueError
        If ``value`` is ``None``.

    Notes
    -----
    The function will attach timezone information using :mod:`zoneinfo` when available, otherwise falls back to :mod:`dateutil.tz`.
    """
    if value is None:
        raise ValueError("date value is None")

    if hasattr(value, "to_pydatetime"):
        dt = value.to_pydatetime()
    elif isinstance(value, datetime):
        dt = value
    else:
        if fmt:
            # explicit format provided (e.g. "%d.%m.%Y %H:%M")
            dt = datetime.strptime(str(value), fmt)
        else:
            dt = dateutil_parser.parse(str(value))

    # if date only (time zero), and hour requested, set hour
    if hour is not None and dt.time() == time(0, 0):
        dt = datetime.combine(dt.date(), time(hour, 0))

    if tz:
        if ZoneInfo is not None:
            dt = dt.replace(tzinfo=ZoneInfo(tz))
        else:
            # fallback: attach offset-less tzinfo via dateutil
            try:
                from dateutil.tz import gettz

                dt = dt.replace(tzinfo=gettz(tz))
            except Exception:
                # as last resort, assume UTC
                from datetime import timezone

                dt = dt.replace(tzinfo=timezone.utc)
    return dt


def relative_notification(start: datetime, days_before: int = 0, minutes_before: int = 0) -> datetime:
    """Compute a notification datetime relative to a start datetime.

    Parameters
    ----------
    start : datetime
        The appointment start datetime.
    days_before : int, optional
        Number of days before ``start`` to schedule the notification.
    minutes_before : int, optional
        Number of minutes before ``start`` to schedule the notification.

    Returns
    -------
    datetime
        The computed notification datetime.
    """
    return start - timedelta(days=days_before, minutes=minutes_before)


def _get_zoneinfo(tz_name: str):
    if ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            pass
    try:
        from dateutil.tz import gettz

        return gettz(tz_name)
    except Exception:
        return None


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def format_de_datetime(
    dt: datetime,
    *,
    tz_name: str = DEFAULT_DISPLAY_TZ,
    fallback_format: str = DE_DATETIME_FORMAT,
) -> DisplayFormatResult:
    """Format a datetime for German display, returning a fallback when conversion fails."""

    warning: Optional[str] = None
    aware = _ensure_aware(dt)
    target_tz = _get_zoneinfo(tz_name)
    if target_tz is None:
        warning = f"Unbekannte Zeitzone: {tz_name}"
        return DisplayFormatResult(aware.isoformat(), warning)
    try:
        localized = aware.astimezone(target_tz)
        return DisplayFormatResult(localized.strftime(fallback_format), None)
    except Exception as exc:  # pragma: no cover - defensive fallback
        warning = f"Konvertierung nach {tz_name} fehlgeschlagen: {exc}"
        return DisplayFormatResult(aware.isoformat(), warning)


def parse_de_datetime(
    date_text: str,
    time_text: str,
    *,
    tz_name: str = DEFAULT_DISPLAY_TZ,
) -> datetime:
    """Parse German date/time fragments into an aware datetime."""

    value = f"{date_text.strip()} {time_text.strip()}"
    return parse_date(value, fmt=DE_DATETIME_FORMAT, tz=tz_name)


def clean_text(text: Optional[str], remove_newlines: bool = True, collapse_whitespace: bool = True) -> Optional[str]:
    """Normalize and clean a text value.

    Parameters
    ----------
    text : str or None
        The text to normalize. If ``None`` returns ``None``.
    remove_newlines : bool, optional
        Replace newline sequences with a single space (default: ``True``).
    collapse_whitespace : bool, optional
        Collapse consecutive whitespace characters into a single space (default: ``True``).

    Returns
    -------
    str or None
        The cleaned text or ``None`` if input was ``None``.

    Examples
    --------
    >>> clean_text('foo\nbar')
    'foo bar'
    """
    if text is None:
        return None
    s = str(text)
    if remove_newlines:
        s = s.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    if collapse_whitespace:
        import re

        s = re.sub(r'\s+', ' ', s)
    return s.strip()
