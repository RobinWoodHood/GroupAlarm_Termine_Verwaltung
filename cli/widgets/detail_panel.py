"""Detail panel widget — shows appointment details with edit mode support."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Sequence

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from framework.appointment import Appointment, convert_reminder_to_minutes
from framework.utils import DEFAULT_DISPLAY_TZ, format_de_datetime, parse_de_datetime
from cli.widgets.state import LabelReference

logger = logging.getLogger(__name__)

DAY_NAMES = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}


@dataclass
class ReminderInput:
    """Structured reminder input with derived minute conversion."""

    value: int | None = None
    unit: str = "minutes"
    minutes_total: int | None = None
    warning: str | None = None


@dataclass
class EditFormState:
    """Editable representation of an appointment for the detail panel."""

    appointment: Appointment
    timezone: str = DEFAULT_DISPLAY_TZ
    label_directory: Sequence[LabelReference] = field(default_factory=list)
    start_date: str = ""
    start_time: str = ""
    end_date: str = ""
    end_time: str = ""
    notification_date: str = ""
    notification_time: str = ""
    reminder: ReminderInput = field(default_factory=ReminderInput)
    label_tokens: List[str] = field(default_factory=list)
    invalid_labels: set[str] = field(default_factory=set)
    conversion_warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.label_directory = list(self.label_directory)
        self._label_lookup = {label.name.lower(): label for label in self.label_directory}

    @classmethod
    def from_appointment(
        cls,
        appt: Appointment,
        *,
        label_directory: Sequence[LabelReference] | None = None,
        display_timezone: str = DEFAULT_DISPLAY_TZ,
    ) -> "EditFormState":
        state = cls(
            appointment=appt,
            timezone=display_timezone,
            label_directory=label_directory or [],
        )
        state._hydrate_from_appointment()
        return state

    def _hydrate_from_appointment(self) -> None:
        self.start_date, self.start_time = self._format_dt(self.appointment.startDate)
        self.end_date, self.end_time = self._format_dt(self.appointment.endDate)
        self.notification_date, self.notification_time = self._format_dt(self.appointment.notificationDate)
        if self.appointment.reminder is not None:
            self.reminder.value = self.appointment.reminder
            self.reminder.minutes_total = self.appointment.reminder
            self.reminder.unit = "minutes"
        self.label_tokens = [str(lid) for lid in self.appointment.labelIDs or []]
        self.invalid_labels = set()

    def _format_dt(self, value: datetime | None) -> tuple[str, str]:
        if value is None:
            return "", ""
        result = format_de_datetime(value, tz_name=self.timezone)
        if result.warning and result.warning not in self.conversion_warnings:
            self.conversion_warnings.append(result.warning)
        parts = result.text.split(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return result.text, ""

    def apply_reminder(self, value: int | str | None, unit: str | None = None) -> None:
        if unit:
            self.reminder.unit = unit
        if value in (None, ""):
            self.reminder.value = None
            self.reminder.minutes_total = None
            self.reminder.warning = None
            return
        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            self.reminder.warning = "Erinnerung benötigt eine Zahl"
            self.reminder.minutes_total = None
            self.reminder.value = None
            return
        unit_name = unit or self.reminder.unit
        self.reminder.value = numeric_value
        try:
            minutes = convert_reminder_to_minutes(numeric_value, unit_name)
            self.reminder.minutes_total = minutes
            self.reminder.unit = unit_name
            self.reminder.warning = None
        except ValueError as exc:
            self.reminder.minutes_total = None
            self.reminder.warning = str(exc)

    def apply_label_tokens(self, tokens: Sequence[str]) -> None:
        normalized = [token.strip() for token in tokens if token and token.strip()]
        self.label_tokens = normalized
        lookup = self._label_lookup
        self.invalid_labels = {token for token in normalized if token.lower() not in lookup}

    def validate_temporal_ordering(self) -> List[str]:
        errors: List[str] = []
        start = self._parse_required(self.start_date, self.start_time, "Startzeit", errors)
        end = self._parse_required(self.end_date, self.end_time, "Endzeit", errors)
        if start and end and end <= start:
            errors.append("Ende muss nach dem Start liegen")
        notification = self._parse_optional(self.notification_date, self.notification_time, errors)
        if notification and start and notification > start:
            errors.append("Benachrichtigung muss vor dem Start liegen")
        return errors

    def _parse_required(
        self,
        date_text: str,
        time_text: str,
        label: str,
        errors: List[str],
    ) -> datetime | None:
        date_value = (date_text or "").strip()
        time_value = (time_text or "").strip() or "00:00"
        if not date_value:
            errors.append(f"{label} fehlt")
            return None
        try:
            return parse_de_datetime(date_value, time_value, tz_name=self.timezone)
        except Exception:
            errors.append(f"{label} ist ungültig")
            return None

    def _parse_optional(
        self,
        date_text: str,
        time_text: str,
        errors: List[str],
    ) -> datetime | None:
        date_value = (date_text or "").strip()
        if not date_value:
            return None
        time_value = (time_text or "").strip() or "00:00"
        try:
            return parse_de_datetime(date_value, time_value, tz_name=self.timezone)
        except Exception:
            errors.append("Benachrichtigung ist ungültig")
            return None


def _format_recurrence(rec: dict) -> str:
    """Format recurrence dict as a human-readable summary."""
    freq = rec.get("frequency", "")
    interval = rec.get("interval", 1)
    days = rec.get("days", [])
    day_str = ", ".join(DAY_NAMES.get(d, str(d)) for d in days) if days else ""
    text = f"Every {interval} {freq}"
    if day_str:
        text += f" on {day_str}"
    count = rec.get("count")
    until = rec.get("until")
    if count:
        text += f" ({count} occurrences)"
    elif until:
        text += f" (until {until})"
    return text


class DetailPanel(Widget):
    """Right-side panel showing appointment details with edit mode support."""

    DEFAULT_CSS = """
    DetailPanel {
        width: 1fr;
        height: 1fr;
        padding: 1 2;
        border-left: solid $primary;
        background: $surface;
    }
    DetailPanel .help-text {
        color: $text-muted;
    }
    DetailPanel .field-label {
        color: $text-muted;
        margin-top: 1;
    }
    DetailPanel .field-modified {
        background: $warning 20%;
    }
    DetailPanel .read-only-field {
        padding: 0 1;
        color: $text;
    }
    DetailPanel .pane-arrow {
        height: 1;
        padding: 0 1;
        color: $text-muted;
    }
    DetailPanel .pane-arrow.active {
        color: $text;
        text-style: bold;
    }
    DetailPanel.is-active {
        border-left: solid $accent;
    }
    """

    class SaveRequested(Message):
        """Posted when the user requests to save changes."""
        def __init__(self, appointment: Appointment, old_values: dict, new_values: dict) -> None:
            super().__init__()
            self.appointment = appointment
            self.old_values = old_values
            self.new_values = new_values

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_appointment: Optional[Appointment] = None
        self._label_service = None
        self._edit_mode: bool = False
        self._create_mode: bool = False
        self._dirty: bool = False
        self._original_values: Dict[str, str] = {}
        self._modified_fields: set = set()
        self._display_tz: str = "Europe/Berlin"
        self._focused: bool = False
        self._arrow_indicator: Static | None = None
        self._focus_target_id: str = "#detail-scroll"
        self._form_state: Optional[EditFormState] = None
        self._label_directory: List[LabelReference] = []

    @property
    def edit_mode(self) -> bool:
        return self._edit_mode

    @property
    def create_mode(self) -> bool:
        return self._create_mode

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def current_appointment(self) -> Optional[Appointment]:
        return self._current_appointment

    def compose(self) -> ComposeResult:
        arrow = Static("← Liste", id="detail-arrow-left", classes="pane-arrow")
        self._arrow_indicator = arrow
        yield arrow
        with VerticalScroll(id="detail-scroll"):
            yield Static(
                "[b]GroupAlarm TUI[/b]\n\n"
                "Select an appointment from the list to view details.\n\n"
                "[dim]Key bindings:[/dim]\n"
                "  [b]↑/↓[/b]     Navigate list\n"
                "  [b]Enter[/b]   Select appointment\n"
                "  [b]e[/b]       Edit mode\n"
                "  [b]Ctrl+T[/b]  Focus date filter\n"
                "  [b]Ctrl+F[/b]  Search\n"
                "  [b]n[/b]       New appointment\n"
                "  [b]d[/b]       Delete selected\n"
                "  [b]x[/b]       Export to Excel\n"
                "  [b]Ctrl+S[/b]  Save changes\n"
                "  [b]Esc[/b]     Cancel edit\n"
                "  [b]F1[/b]      Help\n"
                "  [b]Ctrl +/−[/b] Zoom in/out (terminal)\n"
                "  [b]q[/b]       Quit",
                classes="help-text",
                id="detail-content",
            )

    def show_appointment(self, appt: Appointment, label_service=None, display_tz: str | None = None) -> None:
        """Display appointment in read-only mode."""
        self._current_appointment = appt
        self._label_service = label_service
        if display_tz:
            self._display_tz = display_tz
        self._edit_mode = False
        self._create_mode = False
        self._dirty = False
        self._modified_fields.clear()
        self._render_read_only(appt, label_service)

    def _fmt_dt(self, dt: datetime | None) -> str:
        """Format a datetime in the configured display timezone using the shared formatter."""
        if dt is None:
            return ""
        result = format_de_datetime(dt, tz_name=self._display_tz)
        if result.warning:
            try:
                self.app.notify(result.warning, severity="warning")
            except Exception:
                pass
        return result.text

    def _render_read_only(self, appt: Appointment, label_service=None) -> None:
        """Render all fields as read-only static text with section spacing."""
        content = self.query_one("#detail-content", Static)
        lines = [f"[b]{appt.name}[/b]"]
        lines.append(f"[dim]ID:[/dim] {appt.id}")
        if appt.description:
            lines.append(f"[dim]Beschreibung:[/dim] {appt.description}")
        else:
            lines.append("[dim]Beschreibung:[/dim] —")

        lines.append("")
        lines.append("[b]Zeitplan[/b]")
        lines.append(f"  [dim]Start:[/dim]  {self._fmt_dt(appt.startDate)}")
        lines.append(f"  [dim]Ende:[/dim]   {self._fmt_dt(appt.endDate)}")
        lines.append(f"  [dim]Zone:[/dim]   {appt.timezone}")

        lines.append("")
        lines.append("[b]Labels[/b]")
        if label_service and appt.labelIDs:
            label_names = label_service.get_names_for_ids(appt.labelIDs)
            lines.append(f"  {label_names}")
        elif appt.labelIDs:
            lines.append(f"  {', '.join(str(lid) for lid in appt.labelIDs)}")
        else:
            lines.append("  [dim]—[/dim]")

        lines.append(f"  [dim]Öffentlich:[/dim] {'Ja' if appt.isPublic else 'Nein'}")

        has_notification_section = appt.reminder is not None or appt.notificationDate or appt.feedbackDeadline
        if has_notification_section:
            lines.append("")
            lines.append("[b]Benachrichtigungen[/b]")
            if appt.reminder is not None:
                lines.append(f"  [dim]Erinnerung:[/dim] {appt.reminder} min")
            if appt.notificationDate:
                lines.append(f"  [dim]Benachrichtigung:[/dim] {self._fmt_dt(appt.notificationDate)}")
            if appt.feedbackDeadline:
                lines.append(f"  [dim]Rückmeldefrist:[/dim] {self._fmt_dt(appt.feedbackDeadline)}")

        if appt.participants:
            lines.append("")
            lines.append(f"[dim]Teilnehmer:[/dim] {len(appt.participants)}")

        if appt.recurrence:
            lines.append("")
            lines.append(f"[dim]Wiederholung:[/dim] {_format_recurrence(appt.recurrence)}")

        lines.append("\n[dim]Press [b]e[/b] to edit[/dim]")
        content.update("\n".join(lines))

    def set_label_directory(self, labels: List[LabelReference]) -> None:
        """Store the label directory for autocomplete and validation."""
        self._label_directory = list(labels)

    def enter_edit_mode(self) -> None:
        """Switch to edit mode with editable field display."""
        if not self._current_appointment and not self._create_mode:
            return
        self._edit_mode = True
        self._dirty = False
        self._modified_fields.clear()

        appt = self._current_appointment
        self._original_values = self._get_field_values(appt) if appt else {}
        self._form_state = EditFormState.from_appointment(
            appt,
            label_directory=self._label_directory,
            display_timezone=self._display_tz,
        ) if appt else None
        self._render_edit_form(appt)

    def enter_create_mode(self, defaults: dict) -> None:
        """Switch to create mode with empty/default fields."""
        self._create_mode = True
        self._edit_mode = True
        self._dirty = False
        self._modified_fields.clear()

        now = datetime.now(timezone.utc)
        start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        duration_hours = defaults.get("duration_hours", 4)
        end = start + timedelta(hours=duration_hours)

        self._current_appointment = Appointment(
            name="",
            description="",
            startDate=start,
            endDate=end,
            organizationID=defaults.get("organization_id", 0),
            timezone=defaults.get("timezone", "Europe/Berlin"),
        )
        self._original_values = {}
        self._form_state = EditFormState.from_appointment(
            self._current_appointment,
            label_directory=self._label_directory,
            display_timezone=self._display_tz,
        )
        self._render_edit_form(self._current_appointment)

    def _render_edit_form(self, appt: Optional[Appointment]) -> None:
        """Render fields as an editable form display."""
        content = self.query_one("#detail-content", Static)
        if appt is None:
            content.update("[dim]No appointment selected.[/dim]")
            return

        mode_label = "NEW APPOINTMENT" if self._create_mode else f"EDITING: {appt.name}"
        lines = [f"[b]{mode_label}[/b]"]
        if self._dirty:
            lines[0] += " [yellow]*[/yellow]"
        lines.append("")

        fs = self._form_state
        if fs:
            # Structured split-field rendering
            self._render_field(lines, "name", appt.name or "")
            self._render_field(lines, "description", appt.description or "")
            lines.append("")
            lines.append("[b]Zeitplan[/b]")
            self._render_field(lines, "startDate", f"{fs.start_date} {fs.start_time}")
            self._render_field(lines, "endDate", f"{fs.end_date} {fs.end_time}")
            lines.append("")
            lines.append("[b]Benachrichtigungen[/b]")
            self._render_field(lines, "notificationDate", f"{fs.notification_date} {fs.notification_time}".strip())
            lines.append("")
            lines.append("[b]Erinnerung[/b]")
            reminder_text = ""
            if fs.reminder.value is not None:
                reminder_text = f"{fs.reminder.value} {fs.reminder.unit}"
                if fs.reminder.minutes_total is not None:
                    reminder_text += f" ({fs.reminder.minutes_total} min)"
            self._render_field(lines, "reminder", reminder_text)
            if fs.reminder.warning:
                lines.append(f"  [yellow]⚠ {fs.reminder.warning}[/yellow]")
            lines.append("")
            lines.append("[b]Labels[/b]")
            label_text = ", ".join(fs.label_tokens) if fs.label_tokens else ""
            self._render_field(lines, "labelIDs", label_text)
            if fs.invalid_labels:
                for inv in sorted(fs.invalid_labels):
                    lines.append(f"  [yellow]⚠ Label '{inv}' existiert nicht[/yellow]")
            lines.append("")
            self._render_field(lines, "isPublic", "true" if appt.isPublic else "false")
            self._render_field(lines, "timezone", appt.timezone or "UTC")
            # Inline validation warnings
            temporal_errors = fs.validate_temporal_ordering()
            if temporal_errors:
                lines.append("")
                for err in temporal_errors:
                    lines.append(f"[red]⚠ {err}[/red]")
        else:
            fields = self._get_field_values(appt)
            for field_name, value in fields.items():
                marker = " [yellow]*[/yellow]" if field_name in self._modified_fields else ""
                lines.append(f"[dim]{field_name}:[/dim]{marker} {value}")

        if appt.recurrence:
            lines.append(f"\n[dim]Recurrence (read-only):[/dim] {_format_recurrence(appt.recurrence)}")
        if appt.participants:
            lines.append(f"[dim]Participants (read-only):[/dim] {len(appt.participants)}")

        lines.append("\n[dim]Press [b]Ctrl+S[/b] to save, [b]Esc[/b] to cancel[/dim]")
        if self._dirty:
            lines.append("[yellow]Unsaved changes[/yellow]")

        content.update("\n".join(lines))

    def _render_field(self, lines: List[str], field_name: str, value: str) -> None:
        marker = " [yellow]*[/yellow]" if field_name in self._modified_fields else ""
        lines.append(f"[dim]{field_name}:[/dim]{marker} {value}")

    def _get_field_values(self, appt: Optional[Appointment]) -> Dict[str, str]:
        """Extract editable field values from an appointment."""
        if appt is None:
            return {}
        return {
            "name": appt.name or "",
            "description": appt.description or "",
            "startDate": self._fmt_dt(appt.startDate),
            "endDate": self._fmt_dt(appt.endDate),
            "labelIDs": ",".join(str(lid) for lid in appt.labelIDs) if appt.labelIDs else "",
            "isPublic": "true" if appt.isPublic else "false",
            "reminder": str(appt.reminder) if appt.reminder is not None else "",
            "notificationDate": self._fmt_dt(appt.notificationDate),
            "feedbackDeadline": self._fmt_dt(appt.feedbackDeadline),
            "timezone": appt.timezone or "UTC",
        }

    def update_field(self, field_name: str, value: str) -> None:
        """Update a field value and mark as modified."""
        if not self._current_appointment:
            return

        old_val = self._original_values.get(field_name, "")
        if value != old_val:
            self._modified_fields.add(field_name)
            self._dirty = True
        else:
            self._modified_fields.discard(field_name)
            self._dirty = bool(self._modified_fields)

        self._apply_field_to_appointment(field_name, value)

        # Keep EditFormState in sync with field edits
        if self._form_state:
            self._sync_form_state_field(field_name, value)

        self._render_edit_form(self._current_appointment)

    def _sync_form_state_field(self, field_name: str, value: str) -> None:
        """Propagate a raw field edit into EditFormState."""
        fs = self._form_state
        if fs is None:
            return
        if field_name == "startDate":
            parts = value.strip().split(" ", 1)
            fs.start_date = parts[0] if parts else ""
            fs.start_time = parts[1] if len(parts) > 1 else ""
        elif field_name == "endDate":
            parts = value.strip().split(" ", 1)
            fs.end_date = parts[0] if parts else ""
            fs.end_time = parts[1] if len(parts) > 1 else ""
        elif field_name == "notificationDate":
            parts = value.strip().split(" ", 1)
            fs.notification_date = parts[0] if parts else ""
            fs.notification_time = parts[1] if len(parts) > 1 else ""
        elif field_name == "reminder":
            fs.apply_reminder(value, fs.reminder.unit)
        elif field_name == "labelIDs":
            tokens = [t.strip() for t in value.split(",") if t.strip()]
            fs.apply_label_tokens(tokens)

    def _apply_field_to_appointment(self, field_name: str, value: str) -> None:
        """Apply a field value to the current appointment object."""
        appt = self._current_appointment
        if appt is None:
            return

        from dateutil import parser as dt_parser
        try:
            if field_name == "name":
                appt.name = value
            elif field_name == "description":
                appt.description = value
            elif field_name == "startDate" and value:
                appt.startDate = dt_parser.parse(value)
            elif field_name == "endDate" and value:
                appt.endDate = dt_parser.parse(value)
            elif field_name == "labelIDs":
                if value.strip():
                    appt.labelIDs = [int(x.strip()) for x in value.split(",") if x.strip()]
                else:
                    appt.labelIDs = []
            elif field_name == "isPublic":
                appt.isPublic = value.lower() in ("true", "yes", "1")
            elif field_name == "reminder":
                appt.reminder = int(value) if value.strip() else None
            elif field_name == "notificationDate" and value.strip():
                appt.notificationDate = dt_parser.parse(value)
            elif field_name == "notificationDate":
                appt.notificationDate = None
            elif field_name == "feedbackDeadline" and value.strip():
                appt.feedbackDeadline = dt_parser.parse(value)
            elif field_name == "feedbackDeadline":
                appt.feedbackDeadline = None
            elif field_name == "timezone":
                appt.timezone = value
        except (ValueError, TypeError) as exc:
            logger.debug("Invalid field value %s=%r: %s", field_name, value, exc)

    def get_changes(self) -> tuple[dict, dict]:
        """Return (old_values, new_values) dicts for changed fields only."""
        if not self._current_appointment:
            return {}, {}
        current = self._get_field_values(self._current_appointment)
        old = {}
        new = {}
        for field_name in self._modified_fields:
            old[field_name] = self._original_values.get(field_name, "")
            new[field_name] = current.get(field_name, "")
        return old, new

    def validate_fields(self) -> list[str]:
        """Validate the current appointment fields. Returns a list of error messages."""
        errors = []
        appt = self._current_appointment
        if appt is None:
            return ["No appointment loaded"]
        if not appt.name:
            errors.append("Name is required")
        if not isinstance(appt.startDate, datetime):
            errors.append("Start date is invalid")
        if not isinstance(appt.endDate, datetime):
            errors.append("End date is invalid")
        if isinstance(appt.startDate, datetime) and isinstance(appt.endDate, datetime):
            if appt.endDate <= appt.startDate:
                errors.append("End date must be after start date")
        # EditFormState-powered validations
        if self._form_state:
            temporal = self._form_state.validate_temporal_ordering()
            errors.extend(temporal)
            if self._form_state.reminder.warning:
                errors.append(self._form_state.reminder.warning)
        return errors

    def get_label_warnings(self) -> List[str]:
        """Return label warning messages for the confirmation dialog."""
        if not self._form_state or not self._form_state.invalid_labels:
            return []
        return [f"Label '{name}' existiert nicht" for name in sorted(self._form_state.invalid_labels)]

    def discard_changes(self) -> None:
        """Revert all fields to original values."""
        if self._current_appointment and self._original_values:
            for field_name, value in self._original_values.items():
                self._apply_field_to_appointment(field_name, value)
        self._edit_mode = False
        self._create_mode = False
        self._dirty = False
        self._modified_fields.clear()
        self._form_state = None
        if self._current_appointment:
            self._render_read_only(self._current_appointment, self._label_service)
        else:
            self.show_help()

    def show_help(self) -> None:
        """Display help text when no appointment is selected."""
        self._current_appointment = None
        self._edit_mode = False
        self._create_mode = False
        self._dirty = False
        self._modified_fields.clear()
        content = self.query_one("#detail-content", Static)
        content.update(
            "[b]GroupAlarm TUI[/b]\n\n"
            "Select an appointment from the list to view details.\n\n"
            "[dim]Key bindings:[/dim]\n"
            "  [b]↑/↓[/b]     Navigate list\n"
            "  [b]Enter[/b]   Select appointment\n"
            "  [b]e[/b]       Edit mode\n"
            "  [b]Ctrl+T[/b]  Focus date filter\n"
            "  [b]Ctrl+F[/b]  Search\n"
            "  [b]n[/b]       New appointment\n"
            "  [b]d[/b]       Delete selected\n"
            "  [b]x[/b]       Export to Excel\n"
            "  [b]Ctrl+S[/b]  Save changes\n"
            "  [b]Esc[/b]     Cancel edit\n"
            "  [b]F1[/b]      Help\n"
            "  [b]Ctrl +/−[/b] Zoom in/out (terminal)\n"
            "  [b]q[/b]       Quit"
        )

    def set_focus_state(self, focused: bool) -> None:
        if focused == self._focused:
            return
        self._focused = focused
        self.set_class(focused, "is-active")
        arrow = self._ensure_arrow_indicator()
        if arrow:
            arrow.set_class(focused, "active")
        if focused:
            self._restore_focus_target()
        else:
            self._capture_focus_target()

    def focus_content(self) -> None:
        self._focus_target_id = "#detail-scroll"
        try:
            scroller = self.query_one("#detail-scroll", VerticalScroll)
            scroller.focus()
        except Exception:
            self.focus()

    def _restore_focus_target(self) -> None:
        target_id = self._focus_target_id or "#detail-scroll"
        try:
            widget = self.query_one(target_id)
            widget.focus()
        except Exception:
            self.focus()

    def _capture_focus_target(self) -> None:
        try:
            scroller = self.query_one("#detail-scroll", VerticalScroll)
            if scroller.has_focus:
                self._focus_target_id = "#detail-scroll"
        except Exception:
            pass

    def _ensure_arrow_indicator(self) -> Static | None:
        if self._arrow_indicator is None:
            try:
                self._arrow_indicator = self.query_one("#detail-arrow-left", Static)
            except Exception:
                return None
        return self._arrow_indicator
