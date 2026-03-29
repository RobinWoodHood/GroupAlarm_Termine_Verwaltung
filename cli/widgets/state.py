"""Shared state objects for navigation and filter controls."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Set

VALID_PANELS: Set[str] = {"list", "detail", "filter"}
PREVIEW_LIMIT = 5


@dataclass(frozen=True)
class LabelReference:
    """Lightweight reference used by filter toggles and edit-form suggestions."""

    id: int
    name: str
    color: Optional[str] = None
    assigned_count: int = 0


@dataclass
class NavigationState:
    """Track active panes and focus targets for keyboard navigation."""

    active_panel: Literal["list", "detail", "filter"] = "list"
    focused_widget_id: Optional[str] = None
    list_cursor_key: Optional[int] = None
    filter_focus_index: int = 0

    def set_active_panel(self, panel: str, focused_widget_id: Optional[str] = None) -> None:
        """Execute `set_active_panel`."""
        if panel not in VALID_PANELS:
            raise ValueError(f"Unknown panel '{panel}'")
        self.active_panel = panel  # type: ignore[assignment]
        if focused_widget_id:
            self.focused_widget_id = focused_widget_id
        if panel != "filter":
            self.reset_filter_focus()

    def set_list_cursor(self, appointment_id: Optional[int]) -> None:
        """Execute `set_list_cursor`."""
        self.list_cursor_key = appointment_id

    def focus_filter_index(self, index: int) -> None:
        """Execute `focus_filter_index`."""
        self.active_panel = "filter"
        self.filter_focus_index = max(0, index)

    def advance_filter_focus(self, step: int = 1) -> None:
        """Execute `advance_filter_focus`."""
        self.focus_filter_index(self.filter_focus_index + step)

    def reset_filter_focus(self) -> None:
        """Execute `reset_filter_focus`."""
        self.filter_focus_index = 0


@dataclass
class FilterControls:
    """Persist filter inputs and label preview state."""

    start_date_text: str = ""
    end_date_text: str = ""
    search_text: str = ""
    search_in_description: bool = False
    available_labels: List[LabelReference] = field(default_factory=list)
    selected_label_ids: Set[int] = field(default_factory=set)
    keyboard_order: List[str] = field(
        default_factory=lambda: ["#start-date", "#end-date", "#search-input"]
    )
    preview_limit: int = PREVIEW_LIMIT
    preview_mode: bool = True
    focus_history: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Internal helper for `_post_init__`."""
        self._directory = {label.id: label for label in self.available_labels}
        # Preview mode is unnecessary when the label count is already <= limit
        if len(self.available_labels) <= self.preview_limit:
            self.preview_mode = False

    @property
    def visible_labels(self) -> List[LabelReference]:
        """Execute `visible_labels`."""
        return list(self.available_labels)

    @property
    def hidden_label_count(self) -> int:
        """Execute `hidden_label_count`."""
        if not self.preview_mode:
            return 0
        return max(0, len(self.available_labels) - self.preview_limit)

    def expand_labels(self) -> None:
        """Execute `expand_labels`."""
        self.preview_mode = False

    def collapse_to_preview(self) -> None:
        """Execute `collapse_to_preview`."""
        if len(self.available_labels) > self.preview_limit:
            self.preview_mode = True

    def toggle_label(self, label_id: int) -> None:
        """Execute `toggle_label`."""
        if label_id not in self._directory:
            return
        if label_id in self.selected_label_ids:
            self.selected_label_ids.remove(label_id)
        else:
            self.selected_label_ids.add(label_id)

    def register_shortcut_focus(self, widget_id: str) -> None:
        """Execute `register_shortcut_focus`."""
        self.focus_history.append(widget_id)
        self.expand_labels()

    def set_available_labels(self, labels: List[LabelReference]) -> None:
        """Execute `set_available_labels`."""
        previously_needed_preview = len(self.available_labels) > self.preview_limit
        self.available_labels = labels
        self._directory = {label.id: label for label in labels}
        removed = {lid for lid in self.selected_label_ids if lid not in self._directory}
        if removed:
            self.selected_label_ids -= removed
        if len(labels) <= self.preview_limit:
            self.preview_mode = False
        elif not previously_needed_preview and not self.focus_history and not self.preview_mode:
            # When labels grow beyond the preview limit for the first time, collapse by default
            self.preview_mode = True

    def reset(self) -> None:
        """Execute `reset`."""
        self.start_date_text = ""
        self.end_date_text = ""
        self.search_text = ""
        self.search_in_description = False
        self.selected_label_ids.clear()
        self.collapse_to_preview()
