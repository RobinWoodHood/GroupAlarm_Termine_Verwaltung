"""Import preview workflow screens (file dialog + preview)."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import logging
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Input, Static

from framework.appointment import Appointment
from cli.services.import_service import ImportSession, upload
from cli.screens.import_summary_screen import ImportSummaryScreen
from cli.widgets.appointment_list import AppointmentHighlighted, AppointmentList
from cli.widgets.confirmation_dialog import ConfirmationDialog
from cli.widgets.detail_panel import DetailPanel
from cli.widgets.filter_bar import FilterBar, FilterChanged
from cli.widgets.state import FilterControls, LabelReference


logger = logging.getLogger(__name__)


class ImportFileDialog(ModalScreen[str | None]):
    """Simple modal to collect the import Excel path."""

    DEFAULT_CSS = """
    ImportFileDialog {
        align: center middle;
    }
    #import-file-container {
        width: 80;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: tall $primary;
    }
    #import-file-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #import-file-path {
        margin-bottom: 1;
    }
    #import-file-buttons {
        align: center middle;
        height: auto;
    }
    #import-file-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "confirm", "Import"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="import-file-container"):
            yield Static("Import Excel File", id="import-file-title")
            yield Input(placeholder="Path to Excel file (.xlsx)", id="import-file-path")
            with Horizontal(id="import-file-buttons"):
                yield Button("Import", id="import-file-confirm", variant="primary")
                yield Button("Cancel", id="import-file-cancel")

    def on_mount(self) -> None:
        self.query_one("#import-file-path", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "import-file-confirm":
            self.action_confirm()
        else:
            self.action_cancel()

    def action_confirm(self) -> None:
        value = self.query_one("#import-file-path", Input).value.strip()
        if not value:
            self.app.notify("Please enter a file path.", severity="warning")
            return

        path = Path(value)
        if not path.exists():
            self.app.notify(f"File not found: {value}", severity="error")
            return

        logger.info("Import file selected: %s", path)
        self.dismiss(str(path))

    def action_cancel(self) -> None:
        logger.info("Import file dialog cancelled")
        self.dismiss(None)


class ImportPreviewScreen(Screen):
    """Read-only import preview with filter/navigation/upload flow."""

    DEFAULT_CSS = """
    ImportPreviewScreen {
        layout: vertical;
    }
    #import-banner {
        dock: top;
        height: 1;
        background: darkred;
        color: white;
        text-align: center;
        text-style: bold;
    }
    #import-main-content {
        height: 1fr;
    }
    #import-left-pane {
        width: 3fr;
    }
    ImportPreviewScreen DataTable {
        color: red;
    }
    ImportPreviewScreen DataTable > .datatable--cursor {
        background: darkred;
        color: white;
    }
    ImportPreviewScreen DetailPanel .field-label {
        color: red;
    }
    ImportPreviewScreen DetailPanel .read-only-field {
        color: red;
    }
    """

    BINDINGS = [
        ("ctrl+u", "upload", "Upload"),
        ("escape", "cancel", "Cancel"),
        ("left", "focus_list_panel", "List"),
        ("right", "focus_detail_panel", "Detail"),
        ("ctrl+f", "search", "Search"),
        ("ctrl+t", "focus_start_filter", "Zeitfilter"),
    ]

    def __init__(
        self,
        import_session: ImportSession,
        client,
        label_service,
        config,
        dry_run: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._import_session = import_session
        self._client = client
        self._label_service = label_service
        self._config = config
        self._dry_run = dry_run

        self._display_timezone = (
            self._config.timezone if self._config and self._config.timezone else "Europe/Berlin"
        )
        self._filter_controls = FilterControls(available_labels=self._build_label_directory())
        self._all_appointments = list(import_session.appointments)
        self._filtered_appointments = list(import_session.appointments)
        self._row_key_to_appt: dict[int, Appointment] = {}
        self._next_temp_id = -1

    def compose(self) -> ComposeResult:
        yield Static("⚠ IMPORT PREVIEW", id="import-banner")
        with Horizontal(id="import-main-content"):
            with Vertical(id="import-left-pane"):
                yield FilterBar(
                    labels=self._filter_controls.available_labels,
                    controls=self._filter_controls,
                    id="filter-bar",
                )
                yield AppointmentList(
                    label_service=self._label_service,
                    display_tz=self._display_timezone,
                    id="appt-list",
                )
            yield DetailPanel(id="detail-panel")

    def on_mount(self) -> None:
        source_name = Path(self._import_session.source_path).name
        tier = "Tier 2" if self._import_session.column_mapping_used.startswith("tier2") else "Tier 1"
        banner = self.query_one("#import-banner", Static)
        banner.update(
            f"⚠ IMPORT PREVIEW — {source_name} ({len(self._all_appointments)} appointments) [{tier}]"
        )

        if self._import_session.skipped_rows:
            self.app.notify(
                f"Skipped {len(self._import_session.skipped_rows)} rows (parse errors)",
                severity="warning",
            )

        logger.info(
            "Import preview mounted: source=%s appointments=%d skipped=%d mapping=%s",
            self._import_session.source_path,
            len(self._all_appointments),
            len(self._import_session.skipped_rows),
            self._import_session.column_mapping_used,
        )

        detail = self.query_one("#detail-panel", DetailPanel)
        detail.set_label_directory(self._build_label_directory())

        self._refresh_list()
        self._focus_list_panel()

    def _build_label_directory(self) -> list[LabelReference]:
        if self._label_service:
            return self._label_service.get_directory()
        return []

    def _focus_list_panel(self) -> None:
        try:
            table = self.query_one("#appt-table", DataTable)
            table.focus()
            appt_list = self.query_one("#appt-list", AppointmentList)
            appt_list.set_focus_state(True)
            detail = self.query_one("#detail-panel", DetailPanel)
            detail.set_focus_state(False)
        except Exception:
            pass

    def _focus_detail_panel(self) -> None:
        detail = self.query_one("#detail-panel", DetailPanel)
        detail.focus_content()
        appt_list = self.query_one("#appt-list", AppointmentList)
        appt_list.set_focus_state(False)
        detail.set_focus_state(True)

    def _refresh_list(self) -> None:
        appt_list = self.query_one("#appt-list", AppointmentList)

        display_appointments = []
        self._row_key_to_appt.clear()
        self._next_temp_id = -1

        for appt in self._filtered_appointments:
            display_appt = deepcopy(appt)
            original_id = display_appt.id
            if original_id is None:
                display_appt.id = self._next_temp_id
                self._next_temp_id -= 1
            if display_appt.id is None:
                # Should never happen because None IDs are replaced with temp IDs above.
                continue
            self._row_key_to_appt[display_appt.id] = appt
            display_appointments.append(display_appt)

        appt_list.update_appointments(display_appointments)

        if self._filtered_appointments:
            self._show_detail_for_row_key(next(iter(self._row_key_to_appt.keys())))
        else:
            self.query_one("#detail-panel", DetailPanel).show_help()

    def on_filter_changed(self, _event: FilterChanged) -> None:
        filter_bar = self.query_one("#filter-bar", FilterBar)
        search = (filter_bar.search_text or "").strip().lower()
        selected_labels = set(filter_bar.selected_label_ids)
        include_description = filter_bar.search_in_description

        start_date = self._parse_filter_date(filter_bar.start_date)
        end_date = self._parse_filter_date(filter_bar.end_date)
        if start_date and end_date and start_date > end_date:
            self.app.notify("Start date must be before end date.", severity="warning")
            return

        def matches(appt) -> bool:
            if selected_labels and not (set(appt.labelIDs or []) & selected_labels):
                return False

            appt_date = appt.startDate.date()
            if start_date and appt_date < start_date:
                return False
            if end_date and appt_date > end_date:
                return False

            if search:
                in_name = search in (appt.name or "").lower()
                in_desc = include_description and search in (appt.description or "").lower()
                if not (in_name or in_desc):
                    return False

            return True

        self._filtered_appointments = [a for a in self._all_appointments if matches(a)]
        self._refresh_list()

    def _parse_filter_date(self, value: str):
        text = (value or "").strip()
        if not text:
            return None
        try:
            return datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return None

    def on_appointment_highlighted(self, event: AppointmentHighlighted) -> None:
        self._show_detail_for_row_key(event.appointment_id)

    def _show_detail_for_row_key(self, row_key: int) -> None:
        appt = self._row_key_to_appt.get(row_key)
        if not appt:
            return
        detail = self.query_one("#detail-panel", DetailPanel)
        detail.show_appointment(appt, self._label_service, display_tz=self._display_timezone)

    def action_search(self) -> None:
        self.query_one("#filter-bar", FilterBar).focus_search()

    def action_focus_start_filter(self) -> None:
        self.query_one("#filter-bar", FilterBar).focus_start_date()

    def action_focus_list_panel(self) -> None:
        self._focus_list_panel()

    def action_focus_detail_panel(self) -> None:
        self._focus_detail_panel()

    def action_cancel(self) -> None:
        logger.info("Import preview cancelled by user")
        self.app.pop_screen()

    def _materialize_upload_appointments(self):
        upload_items = []
        for appt in self._filtered_appointments:
            copy_appt = deepcopy(appt)
            if copy_appt.id is not None and copy_appt.id < 0:
                copy_appt.id = None
            upload_items.append(copy_appt)
        return upload_items

    def action_upload(self) -> None:
        if not self._filtered_appointments:
            self.app.notify("No appointments to upload.", severity="warning")
            return

        upload_items = self._materialize_upload_appointments()
        create_count = sum(1 for a in upload_items if a.id is None)
        update_count = len(upload_items) - create_count

        body = (
            f"Upload {len(upload_items)} appointments?\n\n"
            f"- New: {create_count}\n"
            f"- Updates: {update_count}"
        )
        logger.info(
            "Upload requested from preview: total=%d create=%d update=%d dry_run=%s",
            len(upload_items),
            create_count,
            update_count,
            self._dry_run,
        )
        dialog = ConfirmationDialog(
            title="Confirm Upload",
            body=body,
            confirm_label="Upload",
            confirm_key="u",
        )

        def _on_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                logger.info("Upload confirmation cancelled")
                return
            summary = upload(upload_items, self._client, self._dry_run)
            self.app.push_screen(ImportSummaryScreen(summary), self._on_summary_dismissed)

        self.app.push_screen(dialog, _on_confirm)

    def _on_summary_dismissed(self, _result: None) -> None:
        # Summary modal is already dismissed here; now close preview and refresh main screen.
        logger.info("Import summary dismissed; returning to main screen and refreshing")
        self.app.pop_screen()
        screen = self.app.screen
        if hasattr(screen, "_load_appointments"):
            screen._load_appointments()
