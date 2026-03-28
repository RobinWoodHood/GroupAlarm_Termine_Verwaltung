"""Detail panel widget — shows appointment details with edit mode support."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Sequence

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.suggester import Suggester, SuggestFromList
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Input, Static, TextArea

from framework.appointment import Appointment, convert_reminder_to_minutes
from framework.importer_token import ImporterToken
from framework.utils import DEFAULT_DISPLAY_TZ, format_de_datetime, parse_de_datetime
from cli.widgets.state import LabelReference

logger = logging.getLogger(__name__)

DAY_NAMES = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}

# Fields in the order they appear in read-only view (edit mode mirrors this).
# Tuples: (field_id, label_text, placeholder)
EDIT_FIELD_DEFS: list[tuple[str, str, str]] = [
    ("name", "Name:", ""),
    ("description", "Beschreibung:", ""),
    ("startDate", "Start:", "TT.MM.JJJJ HH:MM"),
    ("endDate", "Ende:", "TT.MM.JJJJ HH:MM"),
    ("labels", "Labels (kommagetrennt):", "Label1, Label2"),
    ("participants", "Teilnehmer:", "Name1, Name2"),
    ("isPublic", "Öffentlich:", "Ja / Nein"),
    ("keepLabelParticipantsInSync", "Label-Sync:", "Ja / Nein"),
    ("reminder", "Erinnerung (Minuten):", "z.B. 120"),
    ("notificationDate", "Benachrichtigung:", "TT.MM.JJJJ HH:MM"),
]


class EditInput(Input):
    """Input subclass: Tab accepts the suggestion instead of moving focus.

    Up/Down navigate between form fields.
    """

    BINDINGS = [
        *Input.BINDINGS,
        Binding("tab", "accept_or_next", "Accept suggestion / next field", show=False),
        Binding("up", "focus_prev_field", "Previous field", show=False),
        Binding("down", "focus_next_field", "Next field", show=False),
    ]

    def action_accept_or_next(self) -> None:
        if self.cursor_at_end and self._suggestion:
            self.value = self._suggestion
            self.cursor_position = len(self.value)
        else:
            self.screen.focus_next()

    def action_focus_prev_field(self) -> None:
        focusable = self._edit_focusable()
        if focusable and focusable[0] is not self:
            self.screen.focus_previous()

    def action_focus_next_field(self) -> None:
        focusable = self._edit_focusable()
        if focusable and focusable[-1] is not self:
            self.screen.focus_next()

    def _edit_focusable(self) -> list:
        """Return ordered list of focusable edit widgets in the form."""
        try:
            scroll = self.screen.query_one("#detail-scroll", VerticalScroll)
            return list(scroll.query("EditInput, BoundaryTextArea"))
        except Exception:
            return []


class BoundaryTextArea(TextArea):
    """TextArea that moves focus to adjacent fields at cursor boundaries.

    - Up on the first line → focus previous field
    - Down on the last line → focus next field
    """

    BINDINGS = [
        *TextArea.BINDINGS,
        Binding("up", "cursor_up_or_prev", "Up", show=False),
        Binding("down", "cursor_down_or_next", "Down", show=False),
    ]

    def action_cursor_up_or_prev(self) -> None:
        row, _col = self.cursor_location
        if row == 0:
            focusable = self._edit_focusable()
            if focusable and focusable[0] is not self:
                self.screen.focus_previous()
        else:
            self.action_cursor_up()

    def action_cursor_down_or_next(self) -> None:
        row, _col = self.cursor_location
        if row >= self.document.line_count - 1:
            focusable = self._edit_focusable()
            if focusable and focusable[-1] is not self:
                self.screen.focus_next()
        else:
            self.action_cursor_down()

    def _edit_focusable(self) -> list:
        """Return ordered list of focusable edit widgets in the form."""
        try:
            scroll = self.screen.query_one("#detail-scroll", VerticalScroll)
            return list(scroll.query("EditInput, BoundaryTextArea"))
        except Exception:
            return []


class LabelSuggester(Suggester):
    """Suggest label completions for the last comma-separated token."""

    def __init__(self, label_names: list[str]) -> None:
        super().__init__(use_cache=False, case_sensitive=False)
        self._names = sorted(label_names)

    async def get_suggestion(self, value: str) -> str | None:
        if "," in value:
            prefix, _, current = value.rpartition(",")
            leading = prefix + ", "
            current = current.strip()
        else:
            leading = ""
            current = value.strip()
        if not current:
            return None
        current_lower = current.lower()
        for name in self._names:
            if name.lower().startswith(current_lower):
                return leading + name
        return None


class UserSuggester(Suggester):
    """Suggest user names for the last comma-separated token."""

    def __init__(self, display_names: list[str]) -> None:
        super().__init__(use_cache=False, case_sensitive=False)
        self._names = sorted(display_names)

    async def get_suggestion(self, value: str) -> str | None:
        if "," in value:
            prefix, _, current = value.rpartition(",")
            leading = prefix + ", "
            current = current.strip()
        else:
            leading = ""
            current = value.strip()
        if not current:
            return None
        current_lower = current.lower()
        for name in self._names:
            if name.lower().startswith(current_lower):
                return leading + name
        return None


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
        color: $accent;
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
    DetailPanel .edit-section {
        margin-top: 1;
    }
    DetailPanel .edit-label {
        color: $accent;
        padding: 0 1;
    }
    DetailPanel .edit-input {
        width: 1fr;
        margin: 0 1;
    }
    DetailPanel .edit-input.modified {
        color: red;
    }
    DetailPanel .edit-textarea {
        height: 6;
        width: 1fr;
        margin: 0 1;
    }
    DetailPanel .edit-textarea.modified {
        color: red;
    }
    DetailPanel .edit-hint {
        color: $text-muted;
        margin-top: 1;
        padding: 0 1;
    }
    DetailPanel .edit-warning {
        color: $warning;
        padding: 0 1;
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
        self._user_service = None
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
        self._import_token: Optional[str] = None  # GA-IMPORTER token stripped from description

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
                "  [b]i[/b]       Add GA-IMPORTER tokens\n"
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
        """Render all fields as read-only with .field-label CSS styling."""
        # Separate GA-IMPORTER token from description
        clean_desc, token = ImporterToken.strip_from_text(appt.description)
        self._import_token = token

        # Build Rich markup for the single content Static.
        # Use [bold] style for field labels — the CSS .field-label class
        # with $accent color is applied in the edit-mode mounted widgets.
        # Read-only mode keeps the single-Static approach for speed.
        lines = [f"[b]{appt.name}[/b]"]
        lines.append(f"[dim]ID:[/dim] {appt.id}")
        if clean_desc:
            lines.append(f"[dim]Beschreibung:[/dim] {clean_desc}")
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
        lines.append(f"  [dim]Label-Sync:[/dim] {'Ja' if appt.keepLabelParticipantsInSync else 'Nein'}")

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

        if appt.recurrence:
            lines.append("")
            lines.append(f"[dim]Wiederholung:[/dim] {_format_recurrence(appt.recurrence)}")

        # Direct participants (labelID == 0 or None)
        if appt.participants:
            direct = [p for p in appt.participants if not p.get("labelID")]
            if direct:
                lines.append("")
                lines.append(f"[b]Direkte Teilnehmer[/b] ({len(direct)})")
                for p in direct:
                    name = self._resolve_participant_name(p.get("userID"))
                    lines.append(f"  {name}")

            # Feedback lists
            lines.extend(self._build_feedback_lines(appt.participants))

        lines.append("\n[dim]Press [b]e[/b] to edit[/dim]")

        if self._import_token:
            lines.append(f"\n[dim]{self._import_token}[/dim]")

        try:
            content = self.query_one("#detail-content", Static)
        except Exception:
            # Widget doesn't exist yet (edit UI still mounted); schedule async re-mount
            asyncio.create_task(self._ensure_read_only_content())
            return
        content.update("\n".join(lines))

    def _resolve_participant_name(self, user_id: int | None) -> str:
        """Resolve a user ID to a display name via UserService."""
        if user_id is None:
            return "Unbekannt"
        if self._user_service:
            return self._user_service.get_display_name(user_id)
        return f"User #{user_id}"

    def _build_feedback_lines(self, participants: list[dict]) -> list[str]:
        """Build feedback sub-lists grouped by status.

        Feedback status: 1=Zugesagt, 2=Abgesagt, 0/None=Keine Rückmeldung
        """
        FEEDBACK_LABELS = {1: "Zugesagt", 2: "Abgesagt", 0: "Keine Rückmeldung"}
        groups: dict[int, list[dict]] = {0: [], 1: [], 2: []}
        for p in participants:
            status = p.get("feedback", 0) or 0
            groups.setdefault(status, []).append(p)

        lines: list[str] = []
        # Show user cache warning if UserService is empty
        if self._user_service and not self._user_service.get_directory():
            lines.append("")
            lines.append("[dim italic]⚠ Benutzerdaten nicht verfügbar — IDs werden angezeigt[/dim italic]")

        for status_key in (1, 2, 0):
            group = groups.get(status_key, [])
            if not group:
                continue
            label = FEEDBACK_LABELS.get(status_key, "Unbekannt")
            lines.append("")
            lines.append(f"[b]{label}[/b] ({len(group)})")
            for p in group:
                name = self._resolve_participant_name(p.get("userID"))
                lines.append(f"  {name}")
                msg = p.get("feedbackMessage", "")
                if msg:
                    lines.append(f"    [dim]\"{msg}\"[/dim]")
        return lines

    def set_label_directory(self, labels: List[LabelReference]) -> None:
        """Store the label directory for autocomplete and validation."""
        self._label_directory = list(labels)

    def set_user_service(self, user_service) -> None:
        """Store a reference to the UserService for participant name resolution."""
        self._user_service = user_service

    def _resolve_ids_to_names(self, label_ids: list[int] | None) -> list[str]:
        """Map label IDs to human-readable names using the directory."""
        if not label_ids:
            return []
        lookup = {label.id: label.name for label in self._label_directory}
        return [lookup.get(lid, str(lid)) for lid in label_ids]

    def resolve_labels_from_names(self, names_text: str) -> tuple[list[int], list[str]]:
        """Resolve comma-separated label names to IDs.

        Returns (valid_ids, invalid_names).
        """
        names = [n.strip() for n in names_text.split(",") if n.strip()]
        lookup = {label.name.lower(): label.id for label in self._label_directory}
        valid_ids: list[int] = []
        invalid_names: list[str] = []
        for name in names:
            lid = lookup.get(name.lower())
            if lid is not None:
                valid_ids.append(lid)
            else:
                invalid_names.append(name)
        return valid_ids, invalid_names

    def enter_edit_mode(self) -> None:
        """Switch to edit mode with real Input widgets."""
        if not self._current_appointment and not self._create_mode:
            return
        self._edit_mode = True
        self._dirty = False
        self._modified_fields.clear()

        appt = self._current_appointment
        self._form_state = EditFormState.from_appointment(
            appt,
            label_directory=self._label_directory,
            display_timezone=self._display_tz,
        ) if appt else None

        # Build original values in human-readable format for the Inputs
        self._original_values = self._get_edit_field_values(appt)
        asyncio.create_task(self._mount_edit_ui())

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
            isPublic=False,
            keepLabelParticipantsInSync=True,
        )
        self._form_state = EditFormState.from_appointment(
            self._current_appointment,
            label_directory=self._label_directory,
            display_timezone=self._display_tz,
        )
        self._original_values = self._get_edit_field_values(self._current_appointment)
        asyncio.create_task(self._mount_edit_ui())

    def _get_edit_field_values(self, appt: Optional[Appointment]) -> dict[str, str]:
        """Get field values in the format shown in edit Inputs (human-readable)."""
        if appt is None:
            return {fid: "" for fid, _, _ in EDIT_FIELD_DEFS}
        fs = self._form_state
        label_names = self._resolve_ids_to_names(appt.labelIDs)
        # Strip GA-IMPORTER token from description for editing
        clean_desc, token = ImporterToken.strip_from_text(appt.description)
        self._import_token = token
        # Resolve participant display names
        participant_names = ""
        if appt.participants:
            direct = [p for p in appt.participants if not p.get("labelID")]
            if direct:
                participant_names = ", ".join(
                    self._resolve_participant_name(p.get("userID")) for p in direct
                )
        return {
            "name": appt.name or "",
            "description": clean_desc,
            "startDate": f"{fs.start_date} {fs.start_time}".strip() if fs else self._fmt_dt(appt.startDate),
            "endDate": f"{fs.end_date} {fs.end_time}".strip() if fs else self._fmt_dt(appt.endDate),
            "labels": ", ".join(label_names),
            "participants": participant_names,
            "isPublic": "Ja" if appt.isPublic else "Nein",
            "keepLabelParticipantsInSync": "Ja" if appt.keepLabelParticipantsInSync else "Nein",
            "reminder": str(appt.reminder) if appt.reminder is not None else "",
            "notificationDate": (
                f"{fs.notification_date} {fs.notification_time}".strip()
                if fs else self._fmt_dt(appt.notificationDate)
            ),
        }

    async def _mount_edit_ui(self) -> None:
        """Replace the Static content with editable Input widgets."""
        try:
            scroll = self.query_one("#detail-scroll", VerticalScroll)
        except Exception:
            return
        await scroll.remove_children()

        appt = self._current_appointment
        mode_label = "NEUER TERMIN" if self._create_mode else f"BEARBEITEN: {appt.name if appt else ''}"
        widgets: list[Static | Input | BoundaryTextArea] = [Static(f"[b]{mode_label}[/b]", id="edit-header")]

        label_names = [ref.name for ref in self._label_directory]
        label_suggester = LabelSuggester(label_names) if label_names else None
        user_suggester = None
        if self._user_service:
            user_names = self._user_service.get_all_display_names()
            if user_names:
                user_suggester = UserSuggester(user_names)
        values = self._original_values

        for field_id, label_text, placeholder in EDIT_FIELD_DEFS:
            # Section headers before certain groups
            if field_id == "startDate":
                widgets.append(Static("[b]Zeitplan[/b]", classes="edit-section"))
            elif field_id == "labels":
                widgets.append(Static("[b]Labels[/b]", classes="edit-section"))
            elif field_id == "participants":
                widgets.append(Static("[b]Teilnehmer[/b]", classes="edit-section"))
            elif field_id == "isPublic":
                widgets.append(Static("[b]Optionen[/b]", classes="edit-section"))
            elif field_id == "reminder":
                widgets.append(Static("[b]Benachrichtigungen[/b]", classes="edit-section"))

            widgets.append(Static(label_text, classes="edit-label"))
            if field_id == "description":
                ta = BoundaryTextArea(
                    text=values.get(field_id, ""),
                    id=f"edit-{field_id}",
                    classes="edit-textarea",
                    tab_behavior="focus",
                    show_line_numbers=False,
                    theme="css",
                    soft_wrap=True,
                )
                widgets.append(ta)
            else:
                inp = EditInput(
                    value=values.get(field_id, ""),
                    placeholder=placeholder,
                    id=f"edit-{field_id}",
                    classes="edit-input",
                )
                if field_id == "labels" and label_suggester:
                    inp.suggester = label_suggester
                elif field_id == "participants" and user_suggester:
                    inp.suggester = user_suggester
                widgets.append(inp)

        # Read-only fields
        if appt and appt.recurrence:
            widgets.append(Static(
                f"\n[dim]Wiederholung (nur lesen):[/dim] {_format_recurrence(appt.recurrence)}",
                classes="edit-hint",
            ))

        widgets.append(Static("\n[dim]Ctrl+S speichern, Esc abbrechen[/dim]", classes="edit-hint"))

        await scroll.mount(*widgets)

        # Focus the first Input so user can start typing immediately
        try:
            first_input = self.query_one("#edit-name", EditInput)
            first_input.focus()
        except Exception:
            pass

    def _render_edit_form(self, appt: Optional[Appointment]) -> None:
        """Update the edit header to reflect dirty state (Inputs stay live)."""
        try:
            header = self.query_one("#edit-header", Static)
        except Exception:
            return
        mode_label = "NEUER TERMIN" if self._create_mode else f"BEARBEITEN: {appt.name if appt else ''}"
        if self._dirty:
            mode_label += " [yellow]*[/yellow]"
        header.update(f"[b]{mode_label}[/b]")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Track modified fields and toggle red color on changed Inputs."""
        if not self._edit_mode:
            return
        input_id = event.input.id
        if not input_id or not input_id.startswith("edit-"):
            return
        field_name = input_id[5:]  # strip "edit-" prefix
        original = self._original_values.get(field_name, "")
        if event.value != original:
            self._modified_fields.add(field_name)
            event.input.add_class("modified")
        else:
            self._modified_fields.discard(field_name)
            event.input.remove_class("modified")
        self._dirty = bool(self._modified_fields)
        self._render_edit_form(self._current_appointment)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Track modified state for the description TextArea."""
        if not self._edit_mode:
            return
        ta = event.text_area
        ta_id = ta.id
        if not ta_id or not ta_id.startswith("edit-"):
            return
        field_name = ta_id[5:]
        original = self._original_values.get(field_name, "")
        if ta.text != original:
            self._modified_fields.add(field_name)
            ta.add_class("modified")
        else:
            self._modified_fields.discard(field_name)
            ta.remove_class("modified")
        self._dirty = bool(self._modified_fields)
        self._render_edit_form(self._current_appointment)

    def _read_input_values(self) -> dict[str, str]:
        """Read current values from all edit widgets (Input + TextArea)."""
        values: dict[str, str] = {}
        for field_id, _, _ in EDIT_FIELD_DEFS:
            if field_id == "description":
                try:
                    ta = self.query_one(f"#edit-{field_id}", TextArea)
                    values[field_id] = ta.text
                except Exception:
                    values[field_id] = self._original_values.get(field_id, "")
            else:
                try:
                    inp = self.query_one(f"#edit-{field_id}", Input)
                    values[field_id] = inp.value
                except Exception:
                    values[field_id] = self._original_values.get(field_id, "")
        return values

    def _sync_inputs_to_appointment(self) -> None:
        """Sync all Input widget values to the appointment object and form state."""
        appt = self._current_appointment
        if appt is None:
            return
        values = self._read_input_values()
        fs = self._form_state

        # Name / description (re-append GA-IMPORTER token if present)
        appt.name = values.get("name", "") or ""
        desc = values.get("description", "") or ""
        if self._import_token:
            appt.description = f"{desc}\n{self._import_token}" if desc else self._import_token
        else:
            appt.description = desc

        # Dates — parse German format back to datetime
        for date_field in ("startDate", "endDate", "notificationDate"):
            raw = values.get(date_field, "").strip()
            parts = raw.split(" ", 1)
            date_part = parts[0] if parts else ""
            time_part = parts[1] if len(parts) > 1 else ""
            if fs:
                if date_field == "startDate":
                    fs.start_date, fs.start_time = date_part, time_part
                elif date_field == "endDate":
                    fs.end_date, fs.end_time = date_part, time_part
                elif date_field == "notificationDate":
                    fs.notification_date, fs.notification_time = date_part, time_part
            if date_part:
                try:
                    dt = parse_de_datetime(date_part, time_part or "00:00", tz_name=self._display_tz)
                    setattr(appt, date_field, dt)
                except Exception:
                    pass  # validation will catch this
            elif date_field == "notificationDate":
                appt.notificationDate = None

        # Labels — resolve names to IDs
        labels_text = values.get("labels", "")
        valid_ids, invalid_names = self.resolve_labels_from_names(labels_text)
        appt.labelIDs = valid_ids
        if fs:
            tokens = [n.strip() for n in labels_text.split(",") if n.strip()]
            fs.label_tokens = tokens
            fs.invalid_labels = set(invalid_names)

        # isPublic
        public_val = values.get("isPublic", "").strip().lower()
        appt.isPublic = public_val in ("ja", "true", "yes", "1")

        # keepLabelParticipantsInSync
        sync_val = values.get("keepLabelParticipantsInSync", "").strip().lower()
        appt.keepLabelParticipantsInSync = sync_val in ("ja", "true", "yes", "1")

        # Participants — resolve display names to user IDs
        participants_text = values.get("participants", "").strip()
        if participants_text and self._user_service:
            names = [n.strip() for n in participants_text.split(",") if n.strip()]
            new_participants = []
            for name in names:
                uid = self._user_service.get_user_id_by_display_name(name)
                if uid is not None:
                    new_participants.append({"userID": uid, "labelID": 0})
            # Preserve existing non-direct participants (label-based)
            existing_label_participants = [
                p for p in (appt.participants or []) if p.get("labelID")
            ]
            appt.participants = existing_label_participants + new_participants
        elif not participants_text:
            # Clear direct participants, keep label-based
            existing_label_participants = [
                p for p in (appt.participants or []) if p.get("labelID")
            ]
            appt.participants = existing_label_participants

        # Reminder
        reminder_text = values.get("reminder", "").strip()
        if reminder_text:
            try:
                appt.reminder = int(reminder_text)
                if fs:
                    fs.apply_reminder(reminder_text, "minutes")
            except ValueError:
                appt.reminder = None
                if fs:
                    fs.apply_reminder(reminder_text, "minutes")
        else:
            appt.reminder = None
            if fs:
                fs.apply_reminder(None)

    def get_changes(self) -> tuple[dict, dict]:
        """Return (old_values, new_values) dicts for changed fields only."""
        if not self._current_appointment:
            return {}, {}
        self._sync_inputs_to_appointment()
        current = self._read_input_values()
        old: dict[str, str] = {}
        new: dict[str, str] = {}
        for field_name in self._modified_fields:
            old[field_name] = self._original_values.get(field_name, "")
            new[field_name] = current.get(field_name, "")
        return old, new

    def validate_fields(self) -> list[str]:
        """Validate the current appointment fields. Returns a list of error messages."""
        self._sync_inputs_to_appointment()
        errors: list[str] = []
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
        return [f"Label '{name}' existiert nicht und wird ignoriert"
                for name in sorted(self._form_state.invalid_labels)]

    def discard_changes(self) -> None:
        """Revert all fields to original values and restore read-only view."""
        # Restore original appointment state
        if self._current_appointment and self._original_values:
            appt = self._current_appointment
            appt.name = self._original_values.get("name", appt.name)
            appt.description = self._original_values.get("description", appt.description)
            # Restore label IDs from original names
            orig_labels = self._original_values.get("labels", "")
            if orig_labels:
                valid_ids, _ = self.resolve_labels_from_names(orig_labels)
                appt.labelIDs = valid_ids
            else:
                appt.labelIDs = []
            public_val = self._original_values.get("isPublic", "").strip().lower()
            appt.isPublic = public_val in ("ja", "true", "yes", "1")
            reminder_text = self._original_values.get("reminder", "").strip()
            appt.reminder = int(reminder_text) if reminder_text else None
        was_create = self._create_mode
        self._edit_mode = False
        self._create_mode = False
        self._dirty = False
        self._modified_fields.clear()
        self._form_state = None
        # Restore the Static content into the scroll container
        asyncio.create_task(self._restore_read_only_ui(was_create))

    async def _restore_read_only_ui(self, was_create: bool = False) -> None:
        """Remove edit Inputs and restore the Static content widget."""
        try:
            scroll = self.query_one("#detail-scroll", VerticalScroll)
        except Exception:
            return
        await scroll.remove_children()
        content = Static("", id="detail-content", classes="help-text")
        await scroll.mount(content)
        if was_create or not self._current_appointment:
            self._show_help_content(content)
        else:
            self._render_read_only(self._current_appointment, self._label_service)

    async def _ensure_read_only_content(self) -> None:
        """Ensure #detail-content exists, then re-render the current appointment."""
        try:
            scroll = self.query_one("#detail-scroll", VerticalScroll)
        except Exception:
            return
        await scroll.remove_children()
        content = Static("", id="detail-content", classes="help-text")
        await scroll.mount(content)
        if self._current_appointment:
            self._render_read_only(self._current_appointment, self._label_service)
        else:
            self._show_help_content(content)

    def _show_help_content(self, content: Static) -> None:
        """Write help text into the given Static widget."""
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
            "  [b]i[/b]       Add GA-IMPORTER tokens\n"
            "  [b]Ctrl+S[/b]  Save changes\n"
            "  [b]Esc[/b]     Cancel edit\n"
            "  [b]F1[/b]      Help\n"
            "  [b]Ctrl +/−[/b] Zoom in/out (terminal)\n"
            "  [b]q[/b]       Quit"
        )

    def show_help(self) -> None:
        """Display help text when no appointment is selected."""
        self._current_appointment = None
        self._edit_mode = False
        self._create_mode = False
        self._dirty = False
        self._modified_fields.clear()
        try:
            content = self.query_one("#detail-content", Static)
            self._show_help_content(content)
        except Exception:
            # Content may not exist yet if still in edit UI; schedule restore
            asyncio.create_task(self._restore_read_only_ui(was_create=True))

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
