"""Import summary modal screen."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from cli.services.import_service import ImportSummary


class ImportSummaryScreen(ModalScreen[None]):
    """Display upload summary with failed appointment details."""

    DEFAULT_CSS = """
    ImportSummaryScreen {
        align: center middle;
    }
    #import-summary-container {
        width: 90;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: tall $primary;
    }
    #import-summary-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #import-summary-stats {
        margin-bottom: 1;
    }
    #import-summary-fail-title {
        text-style: bold;
        margin: 1 0 0 0;
    }
    #import-summary-fail-list {
        height: 1fr;
        max-height: 12;
        margin-bottom: 1;
    }
    #import-summary-ok {
        width: 100%;
    }
    """

    BINDINGS = [
        ("escape", "dismiss_screen", "Dismiss"),
        ("enter", "dismiss_screen", "Dismiss"),
    ]

    def __init__(self, summary: ImportSummary, **kwargs) -> None:
        """Initialize the ImportSummaryScreen instance."""
        super().__init__(**kwargs)
        self._summary = summary

    def compose(self) -> ComposeResult:
        """Execute `compose`."""
        title = "Import Summary (DRY-RUN)" if self._summary.dry_run else "Import Summary"
        stats = (
            f"Total: {self._summary.total} | "
            f"Created: {self._summary.created} | "
            f"Updated: {self._summary.updated} | "
            f"Failed: {self._summary.failed}"
        )

        with Vertical(id="import-summary-container"):
            yield Static(title, id="import-summary-title")
            yield Static(stats, id="import-summary-stats")

            if self._summary.failed_results:
                yield Static("Failed appointments:", id="import-summary-fail-title")
                with VerticalScroll(id="import-summary-fail-list"):
                    for result in self._summary.failed_results:
                        appt_name = result.appointment_name or "<unknown>"
                        appt_date = result.appointment_start or "<unknown date>"
                        reason = result.error or "Unknown error"
                        yield Static(f"- {appt_name} ({appt_date}): {reason}")
            else:
                yield Static("All appointments processed successfully.")

            yield Button("OK", id="import-summary-ok", variant="primary")

    def on_button_pressed(self, _event: Button.Pressed) -> None:
        """Handle the `button_pressed` event callback."""
        self.dismiss(None)

    def action_dismiss_screen(self) -> None:
        """Handle the `dismiss_screen` action."""
        self.dismiss(None)
