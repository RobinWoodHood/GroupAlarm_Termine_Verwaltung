from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

REMINDER_MIN_MINUTES = 0
REMINDER_MAX_MINUTES = 10_080  # exactly seven days per API contract
REMINDER_UNIT_FACTORS = {
    "minutes": 1,
    "hours": 60,
    "days": 60 * 24,
    "weeks": 60 * 24 * 7,
}


def validate_reminder_minutes(total_minutes: int) -> None:
    """Ensure reminder minutes remain within the backend's 0–10 080 minute window."""

    if not (REMINDER_MIN_MINUTES <= total_minutes <= REMINDER_MAX_MINUTES):
        raise ValueError(
            f"Reminder must be between {REMINDER_MIN_MINUTES} and {REMINDER_MAX_MINUTES} minutes"
        )


def convert_reminder_to_minutes(value: int, unit: str) -> int:
    unit_key = unit.lower()
    if unit_key not in REMINDER_UNIT_FACTORS:
        raise ValueError(f"Unsupported reminder unit '{unit}'")
    total = int(value) * REMINDER_UNIT_FACTORS[unit_key]
    validate_reminder_minutes(total)
    return total


@dataclass
class Appointment:
    name: str
    description: str
    startDate: datetime
    endDate: datetime
    organizationID: int
    id: Optional[int] = None
    labelIDs: List[int] = field(default_factory=list)
    isPublic: bool = True
    keepLabelParticipantsInSync: bool = True
    reminder: Optional[int] = None  # minutes
    notificationDate: Optional[datetime] = None
    feedbackDeadline: Optional[datetime] = None
    timezone: str = "UTC"
    participants: List[Dict[str, Any]] = field(default_factory=list)
    recurrence: Optional[Dict[str, Any]] = field(default_factory=lambda: None)

    def validate(self) -> None:
        """Validate appointment fields.

        Raises
        ------
        ValueError
            If required fields are missing or invalid (name, start/end dates, organizationID).
        """
        if not self.name:
            raise ValueError("Appointment.name is required")
        if not isinstance(self.startDate, datetime) or not isinstance(self.endDate, datetime):
            raise ValueError("startDate and endDate must be datetime objects")
        if self.endDate <= self.startDate:
            raise ValueError("endDate must be after startDate")
        if not isinstance(self.organizationID, int):
            raise ValueError("organizationID must be an integer")

    def to_api_payload(self) -> Dict[str, Any]:
        """Return the appointment as a JSON-serializable payload for the API.

        The method validates the appointment and returns a dictionary matching
        the GroupAlarm API schema. When ``self.id`` is present it will be included
        in the payload (required for update operations).

        Returns
        -------
        dict
            JSON-serializable payload suitable for POST/PUT requests.
        """
        self.validate()
        payload: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "startDate": self.startDate.astimezone().isoformat(),
            "endDate": self.endDate.astimezone().isoformat(),
            "isPublic": self.isPublic,
            "keepLabelParticipantsInSync": self.keepLabelParticipantsInSync,
            "organizationID": self.organizationID,
            "labelIDs": self.labelIDs,
            "participants": self.participants,
            "timezone": self.timezone,
        }
        if self.reminder is not None:
            payload["reminder"] = self.reminder
        if self.notificationDate is not None:
            payload["notificationDate"] = self.notificationDate.astimezone().isoformat()
        if self.feedbackDeadline is not None:
            payload["feedbackDeadline"] = self.feedbackDeadline.astimezone().isoformat()
        # For update operations the API expects the appointment `id` to be present in the body
        if getattr(self, 'id', None) is not None:
            payload['id'] = self.id
        return payload
