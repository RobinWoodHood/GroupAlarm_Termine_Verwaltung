"""Textual pilot tests for confirmation dialogs and unsaved changes guard."""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone

from cli.app import GroupAlarmApp
from cli.widgets.confirmation_dialog import ConfirmationDialog, UnsavedChangesDialog
from cli.widgets.detail_panel import DetailPanel
from framework.client import GroupAlarmClient
from framework.config import AppConfig
from framework.appointment import Appointment


SAMPLE_LABELS = [
    {"id": 1, "name": "Fire", "color": "#FF0000", "organizationID": 100},
    {"id": 2, "name": "Medical", "color": "#00FF00", "organizationID": 100},
]

SAMPLE_APPOINTMENTS = [
    {
        "id": 10,
        "name": "Training Alpha",
        "description": "First training session",
        "startDate": "2026-03-22T10:00:00+00:00",
        "endDate": "2026-03-22T14:00:00+00:00",
        "organizationID": 100,
        "labelIDs": [1],
        "isPublic": True,
        "keepLabelParticipantsInSync": True,
        "timezone": "Europe/Berlin",
        "participants": [],
        "recurrence": None,
    },
]


def _make_mock_client():
    client = MagicMock(spec=GroupAlarmClient)
    client.token = "test-token"
    client.dry_run = False
    client.list_labels.return_value = SAMPLE_LABELS
    client.list_appointments.return_value = SAMPLE_APPOINTMENTS
    client.update_appointment.return_value = {"id": 10}
    return client


def _make_app(client=None, dry_run=False):
    if client is None:
        client = _make_mock_client()
    config = AppConfig(organization_id=100, date_range_days=30)
    return GroupAlarmApp(client=client, config=config, org_id=100, dry_run=dry_run)


@pytest.mark.asyncio
async def test_confirmation_dialog_confirm():
    """T031: Verify confirmation dialog returns True on confirm."""
    result = None

    def on_dismiss(value):
        nonlocal result
        result = value

    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        dialog = ConfirmationDialog(
            title="Confirm Update",
            body="Name: old → new",
        )
        app.push_screen(dialog, on_dismiss)
        await pilot.pause()
        # Click confirm button
        confirm_btn = app.screen.query_one("#confirm-yes")
        await pilot.click(confirm_btn)
        await pilot.pause()
        assert result is True


@pytest.mark.asyncio
async def test_confirmation_dialog_cancel():
    """T031: Verify confirmation dialog returns False on cancel."""
    result = None

    def on_dismiss(value):
        nonlocal result
        result = value

    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        dialog = ConfirmationDialog(
            title="Confirm Update",
            body="Name: old → new",
        )
        app.push_screen(dialog, on_dismiss)
        await pilot.pause()
        cancel_btn = app.screen.query_one("#confirm-no")
        await pilot.click(cancel_btn)
        await pilot.pause()
        assert result is False


@pytest.mark.asyncio
async def test_unsaved_changes_dialog_save():
    """T032: Verify unsaved changes dialog returns 'save'."""
    result = None

    def on_dismiss(value):
        nonlocal result
        result = value

    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        dialog = UnsavedChangesDialog()
        app.push_screen(dialog, on_dismiss)
        await pilot.pause()
        save_btn = app.screen.query_one("#unsaved-save")
        await pilot.click(save_btn)
        await pilot.pause()
        assert result == "save"


@pytest.mark.asyncio
async def test_unsaved_changes_dialog_discard():
    """T032: Verify unsaved changes dialog returns 'discard'."""
    result = None

    def on_dismiss(value):
        nonlocal result
        result = value

    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        dialog = UnsavedChangesDialog()
        app.push_screen(dialog, on_dismiss)
        await pilot.pause()
        discard_btn = app.screen.query_one("#unsaved-discard")
        await pilot.click(discard_btn)
        await pilot.pause()
        assert result == "discard"


@pytest.mark.asyncio
async def test_unsaved_changes_dialog_cancel():
    """T032: Verify unsaved changes dialog returns 'cancel'."""
    result = None

    def on_dismiss(value):
        nonlocal result
        result = value

    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        dialog = UnsavedChangesDialog()
        app.push_screen(dialog, on_dismiss)
        await pilot.pause()
        cancel_btn = app.screen.query_one("#unsaved-cancel")
        await pilot.click(cancel_btn)
        await pilot.pause()
        assert result == "cancel"


def test_build_update_diff():
    """T031: Verify diff builder shows changed fields."""
    old = {"name": "Old Name", "description": "Old Desc"}
    new = {"name": "New Name", "description": "Old Desc"}
    diff = ConfirmationDialog.build_update_diff(old, new)
    assert "Old Name" in diff
    assert "New Name" in diff
    # Unchanged field should not appear
    assert "description" not in diff


def test_build_update_diff_no_changes():
    """Verify diff with no changes."""
    old = {"name": "Same"}
    new = {"name": "Same"}
    diff = ConfirmationDialog.build_update_diff(old, new)
    assert "No changes" in diff


def test_build_update_diff_groups_sections():
    """T017: Group schedule/reminder changes into dedicated sections."""
    old = {
        "startDate": "21.03.2026 10:00",
        "endDate": "21.03.2026 12:00",
        "reminder": "60",
    }
    new = {
        "startDate": "22.03.2026 09:00",
        "endDate": "22.03.2026 11:00",
        "reminder": "30",
    }
    diff = ConfirmationDialog.build_update_diff(old, new)
    assert "[b]Zeitplan[/b]" in diff
    assert "startDate" in diff
    assert "[b]Erinnerung[/b]" in diff


def test_build_update_diff_surfaces_label_warnings():
    """T017: Label warnings appear beneath the diff when provided."""
    warning = "Label 'Foo' existiert nicht"
    diff = ConfirmationDialog.build_update_diff(
        {"labelIDs": "1"},
        {"labelIDs": "1, Foo"},
        warnings=[warning],
    )
    assert "Hinweise" in diff
    assert warning in diff


def test_build_create_summary():
    """Verify create summary shows all non-empty fields."""
    values = {"name": "Test", "description": "", "organizationID": 100}
    summary = ConfirmationDialog.build_create_summary(values)
    assert "name" in summary
    assert "Test" in summary
    assert "organizationID" in summary
    # Empty description should not appear
    assert "description" not in summary


def test_build_delete_summary():
    """Verify delete summary shows appointment name and period."""
    summary = ConfirmationDialog.build_delete_summary("Training", "2026-03-22", "2026-03-22")
    assert "Training" in summary
    assert "2026-03-22" in summary


@pytest.mark.asyncio
async def test_save_waits_for_confirmation_before_update():
    """T037: Ensure API update is delayed until the confirmation dialog resolves."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        main_screen = app.screen
        detail = main_screen.query_one("#detail-panel", DetailPanel)

        start = datetime(2026, 3, 22, 10, 0, tzinfo=timezone.utc)
        appt = Appointment(
            id=10,
            name="Training Alpha",
            description="Baseline",
            startDate=start,
            endDate=start + timedelta(hours=2),
            organizationID=100,
            labelIDs=[1],
            timezone="UTC",
        )
        detail._current_appointment = appt
        detail._original_values = detail._get_field_values(appt)
        appt.name = "Training Beta"
        detail._modified_fields = {"name"}
        detail._dirty = True
        detail._edit_mode = True
        detail._create_mode = False

        main_screen._appt_service.update = MagicMock()

        main_screen._do_save()
        await pilot.pause()

        main_screen._appt_service.update.assert_not_called()
        assert isinstance(app.screen, ConfirmationDialog)
