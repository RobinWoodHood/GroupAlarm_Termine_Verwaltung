"""Tests for AppointmentService token behavior on manual create."""
from __future__ import annotations

from datetime import datetime, timezone

from cli.services.appointment_service import AppointmentService
from framework.appointment import Appointment
from framework.importer_token import ImporterToken


class _ClientStub:
    def __init__(self):
        self.created: list[Appointment] = []

    def create_appointment(self, appt: Appointment):
        self.created.append(appt)
        return {"id": 123}


def _appt(description: str) -> Appointment:
    start = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return Appointment(
        id=None,
        name="Manual Test",
        description=description,
        startDate=start,
        endDate=start.replace(hour=12),
        organizationID=100,
        timezone="Europe/Berlin",
    )


def test_manual_create_adds_importer_token():
    client = _ClientStub()
    service = AppointmentService(client, organization_id=100)
    appt = _appt("created manually")

    result = service.create(appt)

    assert result["id"] == 123
    assert len(client.created) == 1
    token = ImporterToken.find_in_text(client.created[0].description)
    assert token is not None


def test_manual_create_preserves_existing_token_without_duplication():
    client = _ClientStub()
    service = AppointmentService(client, organization_id=100)
    existing = ImporterToken.create_token()
    appt = _appt(f"already tokenized\n{existing}")

    service.create(appt)

    assert len(client.created) == 1
    created_desc = client.created[0].description
    assert ImporterToken.find_in_text(created_desc) == existing
    assert created_desc.count("GA-IMPORTER") == 1
