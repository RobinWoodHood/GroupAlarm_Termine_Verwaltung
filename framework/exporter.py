from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from openpyxl import Workbook

from .appointment import Appointment
from .importer_token import ImporterToken

logger = logging.getLogger(__name__)

COLUMNS = [
    "name",
    "description",
    "startDate",
    "endDate",
    "organizationID",
    "labelIDs",
    "isPublic",
    "reminder",
    "notificationDate",
    "feedbackDeadline",
    "timezone",
    "groupalarm_id",
    "ga_importer_token",
]


def _format_datetime(dt, tz_name: str) -> str:
    if dt is None:
        return ""
    from dateutil import tz as dateutil_tz
    target_tz = dateutil_tz.gettz(tz_name)
    if target_tz:
        dt = dt.astimezone(target_tz)
    return dt.isoformat()


def export_appointments(
    appointments: List[Appointment],
    output_path: Path,
    timezone: str = "Europe/Berlin",
) -> Path:
    if not appointments:
        raise ValueError("No appointments to export")

    wb = Workbook()
    ws = wb.active
    ws.title = "Appointments"
    ws.append(COLUMNS)

    for appt in appointments:
        clean_desc, token = ImporterToken.strip_from_text(appt.description)
        token = token or ""
        row = [
            appt.name,
            clean_desc,
            _format_datetime(appt.startDate, timezone),
            _format_datetime(appt.endDate, timezone),
            appt.organizationID,
            ",".join(str(lid) for lid in appt.labelIDs) if appt.labelIDs else "",
            appt.isPublic,
            appt.reminder if appt.reminder is not None else "",
            _format_datetime(appt.notificationDate, timezone),
            _format_datetime(appt.feedbackDeadline, timezone),
            appt.timezone,
            appt.id if appt.id is not None else "",
            token,
        ]
        ws.append(row)

    wb.save(output_path)
    logger.info("Exported %d appointments to %s", len(appointments), output_path)
    return output_path
