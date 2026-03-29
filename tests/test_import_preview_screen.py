"""UI tests for ImportPreviewScreen and ImportFileDialog behavior."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from textual.app import App
from textual.widgets import DataTable, Input, Static

from cli.screens.import_preview_screen import ImportFileDialog, ImportPreviewScreen
from cli.services.import_service import ImportSession
from framework.appointment import Appointment
from framework.config import AppConfig


class _LabelServiceStub:
    def get_directory(self):
        return []

    def get_names_for_ids(self, label_ids):
        return ", ".join(str(v) for v in label_ids)


class _ClientStub:
    pass


def _appt(appt_id: int | None, name: str) -> Appointment:
    start = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    return Appointment(
        id=appt_id,
        name=name,
        description=f"Description for {name}",
        startDate=start,
        endDate=start.replace(hour=10),
        organizationID=100,
        labelIDs=[1],
        timezone="Europe/Berlin",
    )


class _PreviewHostApp(App):
    def __init__(self, preview_screen: ImportPreviewScreen):
        super().__init__()
        self._preview_screen = preview_screen

    def on_mount(self) -> None:
        self.push_screen(self._preview_screen)


class _DialogHostApp(App):
    def __init__(self, dialog: ImportFileDialog):
        super().__init__()
        self._dialog = dialog

    def on_mount(self) -> None:
        self.push_screen(self._dialog)


@pytest.mark.asyncio
async def test_preview_mount_navigation_filter_and_cancel(tmp_path):
    source = tmp_path / "sample.xlsx"
    source.write_text("x", encoding="utf-8")
    session = ImportSession(
        source_path=str(source),
        appointments=[_appt(11, "Alpha"), _appt(None, "Beta")],
        skipped_rows=[],
        column_mapping_used="tier1-default",
    )

    screen = ImportPreviewScreen(
        import_session=session,
        client=_ClientStub(),
        label_service=_LabelServiceStub(),
        config=AppConfig(organization_id=100),
        dry_run=True,
    )

    app = _PreviewHostApp(screen)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        banner = app.screen.query_one("#import-banner", Static)
        assert "IMPORT PREVIEW" in str(banner.render())

        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 2

        # Navigation: moving cursor changes highlighted detail appointment.
        await pilot.press("down")
        await pilot.pause()
        detail = app.screen.query_one("#detail-panel")
        assert detail.current_appointment is not None

        # Filtering through search input.
        search_input = app.screen.query_one("#search-input", Input)
        search_input.value = "Beta"
        await pilot.pause()
        await pilot.pause()
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 1

        # Cancel returns to previous screen.
        app.screen.action_cancel()
        await pilot.pause()
        assert not isinstance(app.screen, ImportPreviewScreen)


@pytest.mark.asyncio
async def test_import_file_dialog_validates_path(tmp_path):
    dialog = ImportFileDialog()
    app = _DialogHostApp(dialog)

    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()

        path_input = app.screen.query_one("#import-file-path", Input)
        path_input.value = str(tmp_path / "missing.xlsx")
        await pilot.pause()

        # Confirm with missing file keeps dialog open.
        app.screen.action_confirm()
        await pilot.pause()
        assert isinstance(app.screen, ImportFileDialog)
