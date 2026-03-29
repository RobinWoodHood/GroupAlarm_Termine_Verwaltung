"""UI tests for ImportSummaryScreen."""
from __future__ import annotations

import pytest
from textual.app import App
from textual.widgets import Static

from cli.screens.import_summary_screen import ImportSummaryScreen
from cli.services.import_service import ImportSummary, UploadResult


class _SummaryHostApp(App):
    """Container class `_SummaryHostApp`."""
    def __init__(self, summary_screen: ImportSummaryScreen):
        """Initialize the _SummaryHostApp instance."""
        super().__init__()
        self._summary_screen = summary_screen

    def on_mount(self) -> None:
        """Handle the `mount` event callback."""
        self.push_screen(self._summary_screen)


@pytest.mark.asyncio
async def test_import_summary_screen_displays_counts_and_failures():
    """Test `import_summary_screen_displays_counts_and_failures` behavior."""
    summary = ImportSummary(
        total=3,
        created=1,
        updated=1,
        failed=1,
        dry_run=False,
        results=[
            UploadResult(appointment_name="A", appointment_start="01.04.2026 10:00", action="created", appointment_id=1),
            UploadResult(appointment_name="B", appointment_start="01.04.2026 11:00", action="updated", appointment_id=2),
            UploadResult(appointment_name="C", appointment_start="01.04.2026 12:00", action="failed", error="Validation error"),
        ],
    )

    app = _SummaryHostApp(ImportSummaryScreen(summary))
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        stats = app.screen.query_one("#import-summary-stats", Static)
        assert "Total: 3" in str(stats.render())
        assert "Failed: 1" in str(stats.render())

        fail_title = app.screen.query_one("#import-summary-fail-title", Static)
        assert "Failed appointments" in str(fail_title.render())
        fail_items = list(app.screen.query("#import-summary-fail-list Static"))
        assert any("01.04.2026 12:00" in str(item.render()) for item in fail_items)


@pytest.mark.asyncio
async def test_import_summary_screen_dry_run_title_and_dismiss():
    """Test `import_summary_screen_dry_run_title_and_dismiss` behavior."""
    summary = ImportSummary(total=1, created=1, updated=0, failed=0, dry_run=True, results=[])

    app = _SummaryHostApp(ImportSummaryScreen(summary))
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        title = app.screen.query_one("#import-summary-title", Static)
        assert "DRY-RUN" in str(title.render())

        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, ImportSummaryScreen)
