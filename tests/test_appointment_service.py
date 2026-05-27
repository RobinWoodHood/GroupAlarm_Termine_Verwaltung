"""Tests for AppointmentService token behavior on manual create."""
from __future__ import annotations

from datetime import datetime, timezone

from cli.services.appointment_service import AppointmentService
from framework.appointment import Appointment
from framework.importer_token import ImporterToken


class _ClientStub:
    """Container class `_ClientStub`."""
    def __init__(self):
        """Initialize the _ClientStub instance."""
        self.created: list[Appointment] = []

    def create_appointment(self, appt: Appointment):
        """Execute `create_appointment`."""
        self.created.append(appt)
        return {"id": 123}


def _appt(description: str) -> Appointment:
    """Internal helper for `appt`."""
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
    """Test `manual_create_adds_importer_token` behavior."""
    client = _ClientStub()
    service = AppointmentService(client, organization_id=100)
    appt = _appt("created manually")

    result = service.create(appt)

    assert result["id"] == 123
    assert len(client.created) == 1
    token = ImporterToken.find_in_text(client.created[0].description)
    assert token is not None


def test_manual_create_preserves_existing_token_without_duplication():
    """Test `manual_create_preserves_existing_token_without_duplication` behavior."""
    client = _ClientStub()
    service = AppointmentService(client, organization_id=100)
    existing = ImporterToken.create_token()
    appt = _appt(f"already tokenized\n{existing}")

    service.create(appt)

    assert len(client.created) == 1
    created_desc = client.created[0].description
    assert ImporterToken.find_in_text(created_desc) == existing
    assert created_desc.count("GA-IMPORTER") == 1


class _LabelServiceStub:
    """Stub for LabelService providing label lookups."""

    def __init__(self, labels_by_id: dict[int, dict]):
        """Initialize with label data."""
        self.labels_by_id = labels_by_id

    def get_name(self, label_id: int) -> str:
        """Get label name by ID."""
        label = self.labels_by_id.get(label_id)
        return label["name"] if label else f"Label#{label_id}"

    def get_assignees(self, label_id: int) -> set[int]:
        """Get assignees for a label."""
        label = self.labels_by_id.get(label_id)
        return set(label.get("assignees", [])) if label else set()


def test_group_participants_by_labels_separates_direct_and_label_based():
    """Test grouping separates directly-added from label-based participants."""
    client = _ClientStub()
    service = AppointmentService(client, organization_id=100)
    label_service = _LabelServiceStub({
        1: {"name": "Label1", "assignees": [10, 20]},
        2: {"name": "Label2", "assignees": [20, 30]},
    })

    start = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    appt = Appointment(
        id=1,
        name="Test",
        description="",
        startDate=start,
        endDate=start.replace(hour=12),
        organizationID=100,
        labelIDs=[1, 2],
        participants=[
            {"userID": 1, "labelID": None, "feedback": 1},  # Direct, confirmed
            {"userID": 10, "labelID": 1, "feedback": 1},    # Label1, confirmed
            {"userID": 20, "labelID": 1, "feedback": 2},    # Label1, declined
            {"userID": 20, "labelID": 2, "feedback": 2},    # Label2, declined (duplicate)
            {"userID": 30, "labelID": 2, "feedback": 0},    # Label2, no response
        ],
    )

    grouped = service.group_participants_by_labels(appt, label_service)

    # Check direct participants
    assert len(grouped["direct"]) == 1
    assert grouped["direct"][0]["userID"] == 1

    # Check label-based participants
    assert 1 in grouped["by_label"]
    assert 2 in grouped["by_label"]

    # Check confirmed count (should be unique)
    assert grouped["feedback_counts"]["confirmed"] == 2  # Users 1 and 10

    # Check duplicates
    assert 20 in grouped["duplicate_labels"]
    assert 1 in grouped["duplicate_labels"][20]
    assert 2 in grouped["duplicate_labels"][20]


def test_group_participants_by_labels_counts_unique_users():
    """Test that feedback counts include unique users only (deduped)."""
    client = _ClientStub()
    service = AppointmentService(client, organization_id=100)
    label_service = _LabelServiceStub({
        1: {"name": "Label1", "assignees": [10, 20]},
        2: {"name": "Label2", "assignees": [20, 30]},
    })

    start = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    appt = Appointment(
        id=1,
        name="Test",
        description="",
        startDate=start,
        endDate=start.replace(hour=12),
        organizationID=100,
        labelIDs=[1, 2],
        participants=[
            {"userID": 10, "labelID": 1, "feedback": 1},    # Confirmed in Label1
            {"userID": 20, "labelID": 1, "feedback": 1},    # Confirmed in Label1
            {"userID": 20, "labelID": 2, "feedback": 1},    # Also confirmed in Label2 (duplicate)
            {"userID": 30, "labelID": 2, "feedback": 2},    # Declined in Label2
        ],
    )

    grouped = service.group_participants_by_labels(appt, label_service)

    # Count should be 2 confirmed (users 10 and 20 once each)
    assert grouped["feedback_counts"]["confirmed"] == 2
    # Count should be 1 declined (user 30)
    assert grouped["feedback_counts"]["declined"] == 1
    # Count should be 0 no_response
    assert grouped["feedback_counts"]["no_response"] == 0


def test_group_participants_by_labels_handles_no_labels():
    """Test grouping when appointment has no label-based participants."""
    client = _ClientStub()
    service = AppointmentService(client, organization_id=100)
    label_service = _LabelServiceStub({})

    start = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    appt = Appointment(
        id=1,
        name="Test",
        description="",
        startDate=start,
        endDate=start.replace(hour=12),
        organizationID=100,
        labelIDs=[],
        participants=[
            {"userID": 1, "labelID": None, "feedback": 1},
            {"userID": 2, "labelID": None, "feedback": 2},
        ],
    )

    grouped = service.group_participants_by_labels(appt, label_service)

    assert len(grouped["direct"]) == 2
    assert len(grouped["by_label"]) == 0
    assert grouped["feedback_counts"]["confirmed"] == 1
    assert grouped["feedback_counts"]["declined"] == 1

