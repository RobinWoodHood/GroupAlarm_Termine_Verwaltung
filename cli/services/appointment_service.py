"""Appointment service — bridge between TUI and GroupAlarmClient."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone, date
from typing import Any, Callable, Dict, List, Optional

from framework.appointment import Appointment

logger = logging.getLogger(__name__)


class AppointmentService:
    """Manage the in-memory appointment list with filter/sort/search."""

    def __init__(self, client: Any, organization_id: int, date_range_days: int = 30) -> None:
        self._client = client
        self._organization_id = organization_id
        self._date_range_days = date_range_days
        self._all_appointments: List[Appointment] = []
        self._filtered: List[Appointment] = []
        self._sort_key: str = "startDate"
        self._sort_ascending: bool = True
        self._search_text: str = ""
        self._selected_label_ids: Optional[List[int]] = None
        self._start: Optional[datetime] = None
        self._end: Optional[datetime] = None
        self._filter_start_date: Optional[date] = None
        self._filter_end_date: Optional[date] = None
        self._search_description: bool = False

    def load(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> None:
        now = datetime.now(timezone.utc)
        start_dt = start
        end_dt = end

        if start_dt and end_dt and start_dt > end_dt:
            start_dt, end_dt = end_dt, start_dt

        if start_dt is None and end_dt is not None:
            start_dt = end_dt - timedelta(days=self._date_range_days)
        if end_dt is None and start_dt is not None:
            end_dt = start_dt + timedelta(days=self._date_range_days)

        self._start = start_dt or now
        self._end = end_dt or (now + timedelta(days=self._date_range_days))
        data = self._client.list_appointments(
            start=self._start.isoformat(),
            end=self._end.isoformat(),
            type_="organization",
            organization_id=self._organization_id,
        )
        deduped: List[Appointment] = []
        seen_ids: set[int] = set()
        for raw in data or []:
            appt = self._dict_to_appointment(raw)
            appt_id = appt.id
            if appt_id is not None:
                if appt_id in seen_ids:
                    logger.debug("Skipping duplicate appointment id=%s", appt_id)
                    continue
                seen_ids.add(appt_id)
            deduped.append(appt)

        self._all_appointments = deduped
        logger.info("Loaded %d appointments", len(self._all_appointments))
        self._apply_filters()

    def _dict_to_appointment(self, d: Dict[str, Any]) -> Appointment:
        from dateutil import parser as dt_parser
        return Appointment(
            id=d.get("id"),
            name=d.get("name", ""),
            description=d.get("description", ""),
            startDate=dt_parser.isoparse(d["startDate"]) if d.get("startDate") else datetime.now(timezone.utc),
            endDate=dt_parser.isoparse(d["endDate"]) if d.get("endDate") else datetime.now(timezone.utc),
            organizationID=d.get("organizationID", self._organization_id),
            labelIDs=d.get("labelIDs") or [],
            isPublic=d.get("isPublic", True),
            keepLabelParticipantsInSync=d.get("keepLabelParticipantsInSync", True),
            reminder=d.get("reminder"),
            notificationDate=dt_parser.isoparse(d["notificationDate"]) if d.get("notificationDate") else None,
            feedbackDeadline=dt_parser.isoparse(d["feedbackDeadline"]) if d.get("feedbackDeadline") else None,
            timezone=d.get("timezone", "UTC"),
            participants=d.get("participants") or [],
            recurrence=d.get("recurrence"),
        )

    def set_label_filter(self, label_ids: Optional[List[int]]) -> None:
        self._selected_label_ids = label_ids
        self._apply_filters()

    def set_search(self, text: str, include_description: Optional[bool] = None) -> None:
        self._search_text = text.strip().lower()
        if include_description is not None:
            self._search_description = include_description
        self._apply_filters()

    def set_date_filter(self, start: Optional[date], end: Optional[date]) -> None:
        self._filter_start_date = start
        self._filter_end_date = end
        self._apply_filters()

    def toggle_sort(self) -> str:
        if self._sort_key == "startDate":
            self._sort_key = "name"
        else:
            self._sort_key = "startDate"
        self._apply_filters()
        return self._sort_key

    def _apply_filters(self) -> None:
        result = list(self._all_appointments)

        # Label filter
        if self._selected_label_ids:
            selected = set(self._selected_label_ids)
            result = [a for a in result if set(a.labelIDs) & selected]

        # Search filter
        if self._search_text:
            result = [
                a for a in result
                if self._search_text in a.name.lower()
                or (
                    self._search_description
                    and self._search_text in (a.description or "").lower()
                )
            ]

        # Date filter (inclusive, compares appointment start date)
        if self._filter_start_date or self._filter_end_date:
            result = [a for a in result if self._within_date_range(a)]

        # Sort
        if self._sort_key == "name":
            result.sort(key=lambda a: a.name.lower(), reverse=not self._sort_ascending)
        else:
            result.sort(key=lambda a: a.startDate, reverse=not self._sort_ascending)

        self._filtered = result

    def _within_date_range(self, appointment: Appointment) -> bool:
        appt_date = appointment.startDate.date()
        if self._filter_start_date and appt_date < self._filter_start_date:
            return False
        if self._filter_end_date and appt_date > self._filter_end_date:
            return False
        return True

    @property
    def appointments(self) -> List[Appointment]:
        return list(self._filtered)

    @property
    def all_appointments(self) -> List[Appointment]:
        return list(self._all_appointments)

    def get_by_id(self, appt_id: int) -> Optional[Appointment]:
        for a in self._all_appointments:
            if a.id == appt_id:
                return a
        return None

    def update(self, appt: Appointment, strategy: str = "all") -> dict:
        """Update an appointment via the client and refresh local cache."""
        result = self._client.update_appointment(appt, strategy=strategy)
        logger.info("Updated appointment %s (strategy=%s)", appt.id, strategy)
        return result

    def create(self, appt: Appointment) -> dict:
        """Create a new appointment via the client."""
        result = self._client.create_appointment(appt)
        logger.info("Created appointment: %s", appt.name)
        return result

    def delete(self, appt_id: int, strategy: str = "all", time_: Optional[str] = None) -> None:
        """Delete an appointment via the client."""
        self._client.delete_appointment(appt_id, strategy=strategy, time_=time_)
        logger.info("Deleted appointment %s (strategy=%s)", appt_id, strategy)

    def add_missing_tokens(self) -> tuple[int, int, list[str]]:
        """Add GA-IMPORTER tokens to all filtered appointments that lack one.

        Each modified appointment is immediately pushed to the API.

        Returns
        -------
        tuple[int, int, list[str]]
            ``(updated_count, skipped_count, errors)``
        """
        from framework.importer_token import ImporterToken

        updated = 0
        skipped = 0
        errors: list[str] = []
        for appt in self._filtered:
            if ImporterToken.find_in_text(appt.description):
                skipped += 1
                continue
            ImporterToken.ensure_token(appt)
            try:
                self._client.update_appointment(appt)
                updated += 1
            except Exception as exc:
                errors.append(f"{appt.name} (ID {appt.id}): {exc}")
                logger.error("Failed to add token to %s: %s", appt.id, exc)
        return updated, skipped, errors
