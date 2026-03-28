"""Confirmation dialogs for mutations — diff view, unsaved changes guard, recurrence strategy."""
from __future__ import annotations

from typing import ClassVar, Dict, List, Optional

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Label


def _underline_key(label: str, key: str) -> str:
    """Return *label* with the first occurrence of *key* underlined."""
    idx = label.lower().find(key.lower())
    if idx == -1:
        return f"[u]{key.upper()}[/u] {label}"
    return label[:idx] + f"[u]{label[idx]}[/u]" + label[idx + 1:]

SECTION_MAP = {
    "name": "Grunddaten",
    "description": "Grunddaten",
    "timezone": "Grunddaten",
    "startDate": "Zeitplan",
    "endDate": "Zeitplan",
    "notificationDate": "Benachrichtigungen",
    "feedbackDeadline": "Benachrichtigungen",
    "reminder": "Erinnerung",
    "labelIDs": "Labels",
    "labels": "Labels",
    "isPublic": "Grunddaten",
    "keepLabelParticipantsInSync": "Labels",
    "participants": "Teilnehmer",
}
SECTION_ORDER = [
    "Grunddaten",
    "Zeitplan",
    "Benachrichtigungen",
    "Erinnerung",
    "Labels",
    "Teilnehmer",
    "Weitere Felder",
]
DEFAULT_SECTION = "Weitere Felder"


class ConfirmationDialog(ModalScreen[bool]):
    """Modal confirmation dialog showing a diff summary before mutations.

    For updates: side-by-side old→new diff.
    For creates: structured payload summary.
    For deletes: name + irreversibility warning.
    """

    DEFAULT_CSS = """
    ConfirmationDialog {
        align: center middle;
    }
    #confirmation-container {
        width: 80;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: tall $primary;
    }
    #confirmation-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #confirmation-body {
        max-height: 60%;
        overflow-y: auto;
        margin-bottom: 1;
    }
    #confirmation-warning {
        color: $error;
        text-style: bold;
        margin-bottom: 1;
    }
    #confirmation-buttons {
        align: center middle;
        height: auto;
    }
    #confirmation-buttons Button {
        margin: 0 2;
    }
    #confirmation-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        title: str,
        body: str,
        warning: str = "",
        confirm_label: str = "Save",
        confirm_key: str = "",
        cancel_label: str = "Cancel",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._body = body
        self._warning = warning
        self._confirm_label = confirm_label
        self._cancel_label = cancel_label
        # Derive shortcut key from the first letter of confirm_label
        self._confirm_key = (confirm_key or confirm_label[0]).lower()

    def compose(self) -> ComposeResult:
        confirm_display = _underline_key(self._confirm_label, self._confirm_key)
        with Vertical(id="confirmation-container"):
            yield Static(self._title, id="confirmation-title")
            yield Static(self._body, id="confirmation-body")
            if self._warning:
                yield Static(self._warning, id="confirmation-warning")
            with Horizontal(id="confirmation-buttons"):
                yield Button(confirm_display, id="confirm-yes", variant="error")
                yield Button("Cancel", id="confirm-no", variant="primary")
            yield Static(
                f"[dim]{self._confirm_key.upper()} = {self._confirm_label}  ·  Esc = Cancel[/dim]",
                id="confirmation-hint",
            )

    def on_mount(self) -> None:
        # Dynamically bind the confirm key
        self._bindings.bind(self._confirm_key, "confirm", self._confirm_label, show=False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")

    @staticmethod
    def build_update_diff(
        old_values: Dict[str, str],
        new_values: Dict[str, str],
        *,
        warnings: Optional[List[str]] = None,
    ) -> str:
        """Build a grouped diff summary for the confirmation dialog."""

        sections: Dict[str, List[tuple[str, str, str]]] = {}
        keys = sorted(set(old_values) | set(new_values))
        for key in keys:
            old_val = str(old_values.get(key, "") or "")
            new_val = str(new_values.get(key, "") or "")
            if old_val == new_val:
                continue
            section = SECTION_MAP.get(key, DEFAULT_SECTION)
            sections.setdefault(section, []).append((key, old_val or "—", new_val or "—"))

        lines: List[str] = []
        for section in SECTION_ORDER:
            entries = sections.get(section)
            if not entries:
                continue
            lines.append(f"[b]{section}[/b]")
            for field, old_val, new_val in entries:
                lines.append(f"  [dim]{field}[/dim]")
                lines.append(f"    [red]- {old_val}[/red]")
                lines.append(f"    [green]+ {new_val}[/green]")
            lines.append("")

        if lines and not lines[-1]:
            lines.pop()

        warning_lines = [w for w in (warnings or []) if w]
        if warning_lines:
            if lines:
                lines.append("")
            else:
                lines.append("[dim]No changes detected.[/dim]")
                lines.append("")
            lines.append("[yellow]Hinweise[/yellow]")
            for warning in warning_lines:
                lines.append(f"  • {warning}")

        if not lines:
            return "[dim]No changes detected.[/dim]"
        return "\n".join(lines)

    @staticmethod
    def build_create_summary(values: dict) -> str:
        """Build a structured payload summary for create confirmation."""
        lines = []
        for key, val in values.items():
            if val not in (None, "", []):
                lines.append(f"[b]{key}[/b]: {val}")
        return "\n".join(lines) if lines else "[dim]Empty payload.[/dim]"

    @staticmethod
    def build_delete_summary(name: str, start: str, end: str) -> str:
        """Build a delete confirmation body."""
        return (
            f"[b]Appointment:[/b] {name}\n"
            f"[b]Period:[/b] {start} → {end}\n"
        )


class UnsavedChangesDialog(ModalScreen[str]):
    """Modal dialog for unsaved changes — Save, Discard, or Cancel."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("s", "do_save", "Save", show=False),
        Binding("d", "do_discard", "Discard", show=False),
        Binding("escape", "do_cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    UnsavedChangesDialog {
        align: center middle;
    }
    #unsaved-container {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: tall $warning;
    }
    #unsaved-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #unsaved-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    #unsaved-buttons {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    #unsaved-buttons Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="unsaved-container"):
            yield Static("[b]Unsaved Changes[/b]", id="unsaved-title")
            yield Static("You have unsaved changes. What would you like to do?")
            with Horizontal(id="unsaved-buttons"):
                yield Button(_underline_key("Save", "s"), id="unsaved-save", variant="success")
                yield Button(_underline_key("Discard", "d"), id="unsaved-discard", variant="error")
                yield Button(_underline_key("Cancel", "c"), id="unsaved-cancel", variant="primary")
            yield Static("[dim]S = Save  ·  D = Discard  ·  Esc = Cancel[/dim]", id="unsaved-hint")

    def action_do_save(self) -> None:
        self.dismiss("save")

    def action_do_discard(self) -> None:
        self.dismiss("discard")

    def action_do_cancel(self) -> None:
        self.dismiss("cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        result_map = {
            "unsaved-save": "save",
            "unsaved-discard": "discard",
            "unsaved-cancel": "cancel",
        }
        self.dismiss(result_map.get(event.button.id, "cancel"))


class RecurrenceStrategyDialog(ModalScreen[str]):
    """Modal dialog for choosing recurrence strategy (single/upcoming/all)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("t", "choose_single", "This occurrence", show=False),
        Binding("u", "choose_upcoming", "This and upcoming", show=False),
        Binding("a", "choose_all", "All occurrences", show=False),
        Binding("escape", "choose_cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    RecurrenceStrategyDialog {
        align: center middle;
    }
    #strategy-container {
        width: 50;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: tall $primary;
    }
    #strategy-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #strategy-buttons {
        height: auto;
        margin-top: 1;
    }
    #strategy-buttons Button {
        width: 100%;
        margin-bottom: 1;
    }
    #strategy-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="strategy-container"):
            yield Static("[b]Recurring Appointment[/b]", id="strategy-title")
            yield Static("This is a recurring appointment. Choose the scope:")
            with Vertical(id="strategy-buttons"):
                yield Button(_underline_key("This occurrence only", "t"), id="strategy-single", variant="primary")
                yield Button(_underline_key("This and upcoming", "u"), id="strategy-upcoming", variant="warning")
                yield Button(_underline_key("All occurrences", "a"), id="strategy-all", variant="error")
                yield Button(_underline_key("Cancel", "c"), id="strategy-cancel")
            yield Static("[dim]T = This only  ·  U = Upcoming  ·  A = All  ·  Esc = Cancel[/dim]", id="strategy-hint")

    def action_choose_single(self) -> None:
        self.dismiss("single")

    def action_choose_upcoming(self) -> None:
        self.dismiss("upcoming")

    def action_choose_all(self) -> None:
        self.dismiss("all")

    def action_choose_cancel(self) -> None:
        self.dismiss("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        result_map = {
            "strategy-single": "single",
            "strategy-upcoming": "upcoming",
            "strategy-all": "all",
            "strategy-cancel": "",
        }
        self.dismiss(result_map.get(event.button.id, ""))
