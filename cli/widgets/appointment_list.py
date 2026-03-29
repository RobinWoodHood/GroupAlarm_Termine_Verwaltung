"""AppointmentList widget — DataTable showing appointments."""
from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Static

from framework.appointment import Appointment
from framework.utils import format_de_datetime


class AppointmentSelected(Message):
    """Posted when an appointment is selected."""

    def __init__(self, appointment_id: int) -> None:
        """Initialize the AppointmentSelected instance."""
        super().__init__()
        self.appointment_id = appointment_id


class AppointmentHighlighted(Message):
    """Posted when the cursor moves to a different appointment row."""

    def __init__(self, appointment_id: int) -> None:
        """Initialize the AppointmentHighlighted instance."""
        super().__init__()
        self.appointment_id = appointment_id


class AppointmentList(Widget):
    """Scrollable appointment list as a DataTable."""

    DEFAULT_CSS = """
    AppointmentList {
        height: 1fr;
    }
    AppointmentList .pane-arrow {
        height: 1;
        padding: 0 1;
        text-align: right;
        color: $text-muted;
    }
    AppointmentList .pane-arrow.active {
        color: $text;
        text-style: bold;
    }
    AppointmentList DataTable {
        height: 1fr;
    }
    AppointmentList DataTable > .datatable--cursor {
        background: $accent 35%;
        color: $text;
        text-style: bold;
    }
    AppointmentList.is-active DataTable > .datatable--cursor {
        background: $accent;
        color: $surface;
    }
    """

    def __init__(self, label_service=None, display_tz: str = "Europe/Berlin", **kwargs) -> None:
        """Initialize the AppointmentList instance."""
        super().__init__(**kwargs)
        self._label_service = label_service
        self._appointments: list[Appointment] = []
        self._display_tz = display_tz
        self._focused: bool = False
        self._arrow_indicator: Static | None = None

    def compose(self) -> ComposeResult:
        """Execute `compose`."""
        arrow = Static("→ Detail", id="list-arrow-right", classes="pane-arrow")
        self._arrow_indicator = arrow
        yield arrow

        table = DataTable(id="appt-table", cursor_type="row")
        table.zebra_stripes = True
        table.add_columns("Name", "Start", "End", "Labels")
        yield table

    def _fmt_dt(self, dt: datetime | None) -> str:
        """Internal helper for `fmt_dt`."""
        if dt is None:
            return ""
        result = format_de_datetime(dt, tz_name=self._display_tz)
        if result.warning:
            # Dispatch warning toast via app if available
            try:
                self.app.notify(result.warning, severity="warning")
            except Exception:
                pass
        return result.text

    def update_appointments(self, appointments: list[Appointment]) -> None:
        """Execute `update_appointments`."""
        self._appointments = appointments
        table = self.query_one("#appt-table", DataTable)
        table.clear()
        for appt in appointments:
            name = appt.name
            if len(name) > 40:
                name = name[:37] + "..."
            start = self._fmt_dt(appt.startDate)
            end = self._fmt_dt(appt.endDate)
            labels = ""
            if self._label_service and appt.labelIDs:
                labels = self._label_service.get_names_for_ids(appt.labelIDs)
            elif appt.labelIDs:
                labels = ", ".join(str(lid) for lid in appt.labelIDs)
            table.add_row(name, start, end, labels, key=str(appt.id))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle the `data_table_row_selected` event callback."""
        if event.row_key and event.row_key.value:
            try:
                appt_id = int(event.row_key.value)
                self.post_message(AppointmentSelected(appt_id))
            except (ValueError, TypeError):
                pass

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle the `data_table_row_highlighted` event callback."""
        if event.row_key and event.row_key.value:
            try:
                appt_id = int(event.row_key.value)
                self.post_message(AppointmentHighlighted(appt_id))
            except (ValueError, TypeError):
                pass

    def get_appointment_at_cursor(self) -> int | None:
        """Execute `get_appointment_at_cursor`."""
        table = self.query_one("#appt-table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            return int(row_key.value)
        except Exception:
            return None

    def set_focus_state(self, focused: bool) -> None:
        """Execute `set_focus_state`."""
        if focused == self._focused:
            return
        self._focused = focused
        self.set_class(focused, "is-active")
        arrow = self._ensure_arrow_indicator()
        if arrow:
            arrow.set_class(focused, "active")

    def _ensure_arrow_indicator(self) -> Static | None:
        """Internal helper for `ensure_arrow_indicator`."""
        if self._arrow_indicator is None:
            try:
                self._arrow_indicator = self.query_one("#list-arrow-right", Static)
            except Exception:
                return None
        return self._arrow_indicator
