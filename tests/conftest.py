import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from cli.app import GroupAlarmApp
from framework.client import GroupAlarmClient
from framework.config import AppConfig

FIXTURE_PATH = Path(__file__).parent / "data" / "tui_sample.json"
DEFAULT_ORG_ID = 100


def _load_fixtures() -> Dict[str, Any]:
    """Internal helper for `load_fixtures`."""
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _transform_appointment(record: Dict[str, Any]) -> Dict[str, Any]:
    """Internal helper for `transform_appointment`."""
    payload: Dict[str, Any] = {
        "id": record["id"],
        "name": record["title"],
        "description": record.get("description", ""),
        "startDate": record["start"],
        "endDate": record["end"],
        "organizationID": DEFAULT_ORG_ID,
        "labelIDs": record.get("labels", []),
        "isPublic": True,
        "keepLabelParticipantsInSync": True,
        "timezone": record.get("timezone", "UTC"),
        "participants": [],
        "recurrence": None,
    }
    if record.get("notification"):
        payload["notificationDate"] = record["notification"]
    if record.get("reminderMinutes") is not None:
        payload["reminder"] = record["reminderMinutes"]
    return payload


@pytest.fixture(scope="session")
def tui_sample_data() -> Dict[str, Any]:
    """Execute `tui_sample_data`."""
    return _load_fixtures()


@pytest.fixture
def mock_client(tui_sample_data) -> GroupAlarmClient:
    """Execute `mock_client`."""
    client = MagicMock(spec=GroupAlarmClient)
    client.token = "test-token"
    client.dry_run = False
    client.list_labels.return_value = tui_sample_data["labels"]
    client.list_appointments.return_value = [
        _transform_appointment(row) for row in tui_sample_data["appointments"]
    ]
    return client


@pytest_asyncio.fixture
async def pilot_app(mock_client) -> Tuple[Any, GroupAlarmApp]:
    """Run the Textual pilot once per test for keyboard-centric suites."""

    config = AppConfig(organization_id=DEFAULT_ORG_ID, date_range_days=30)
    app = GroupAlarmApp(client=mock_client, config=config, org_id=DEFAULT_ORG_ID, dry_run=True)
    async with app.run_test(size=(120, 40)) as pilot:
        yield pilot, app


@pytest.fixture
def focus_widget():
    """Execute `focus_widget`."""
    def _focus(app: GroupAlarmApp, selector: str):
        """Internal helper for `focus`."""
        widget = app.screen.query_one(selector)
        widget.focus()
        return widget

    return _focus
