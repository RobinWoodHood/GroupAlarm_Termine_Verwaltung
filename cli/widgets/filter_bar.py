"""FilterBar widget — label toggle list, date range inputs, search."""
from __future__ import annotations

import asyncio
from datetime import date
from typing import Iterable, Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.events import DescendantBlur
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Switch

from cli.widgets.state import FilterControls, LabelReference


class FilterChanged(Message):
    """Posted when any filter changes."""


class FilterBar(Widget):
    """Filter bar with dynamic label toggles, date range, and search toggles."""

    DEFAULT_CSS = """
    FilterBar {
        layout: vertical;
        height: auto;
        max-height: 14;
        dock: top;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $primary;
    }
    FilterBar .filter-section {
        height: auto;
        max-height: 3;
        padding: 0 1;
    }
    FilterBar #label-scroll {
        height: auto;
        max-height: 9;
        scrollbar-size: 1 1;
    }
    FilterBar #label-buttons {
        layout: grid;
        grid-size: 5;
        grid-gutter: 0 1;
        height: auto;
        width: 1fr;
    }
    FilterBar .filter-label {
        width: auto;
        padding: 0 1 0 0;
        color: $text-muted;
    }
    FilterBar Input {
        width: 20;
        margin: 0 1 0 0;
    }
    FilterBar #search-input {
        width: 30;
    }
    FilterBar Switch {
        margin: 0 1 0 0;
    }
    FilterBar .label-toggle {
        min-width: 12;
        height: 3;
        margin: 0;
        border: none;
        padding: 0;
        background: $surface-darken-1;
        color: $text-muted;
    }
    FilterBar .label-toggle.active {
        background: $primary;
        color: $text;
        text-style: bold;
    }
    FilterBar #until-end-year-btn {
        min-width: 14;
        height: 3;
        margin: 0 1 0 0;
    }
    """

    search_text: reactive[str] = reactive("", init=False)
    search_description_enabled: reactive[bool] = reactive(False, init=False)

    def __init__(
        self,
        labels: Sequence[LabelReference | dict] | None = None,
        default_label_ids: Sequence[int] | None = None,
        default_start: str = "",
        default_end: str = "",
        include_description: bool = False,
        controls: FilterControls | None = None,
        **kwargs,
    ) -> None:
        """Initialize the FilterBar instance."""
        super().__init__(**kwargs)
        self.controls = controls or FilterControls()
        self._default_start = default_start
        self._default_end = default_end
        self._focused = False

        if default_label_ids:
            self.controls.selected_label_ids.update(int(lid) for lid in default_label_ids)

        self.controls.start_date_text = self.controls.start_date_text or default_start
        self.controls.end_date_text = self.controls.end_date_text or default_end
        self.controls.search_text = self.controls.search_text or ""
        self.controls.search_in_description = include_description or self.controls.search_in_description

        self.search_text = self.controls.search_text
        self._search_description = self.controls.search_in_description
        self.search_description_enabled = self._search_description

        if labels:
            refs = self._normalize_label_refs(labels)
            self.controls.set_available_labels(refs)

    def compose(self) -> ComposeResult:
        """Execute `compose`."""
        yield Label("Labels:", classes="filter-label")
        with VerticalScroll(id="label-scroll"):
            with Horizontal(id="label-buttons"):
                for button in self._iter_label_buttons():
                    yield button
        with Horizontal(classes="filter-section"):
            yield Label("Datumsfilter (TT.MM.JJJJ):", classes="filter-label")
            yield Input(
                value=self.controls.start_date_text or self._default_start,
                placeholder="Start (TT.MM.JJJJ)",
                restrict=r"[0-9\.]*",
                id="start-date",
            )
            yield Input(
                value=self.controls.end_date_text or self._default_end,
                placeholder="Ende (TT.MM.JJJJ)",
                restrict=r"[0-9\.]*",
                id="end-date",
            )
            yield Button("Bis Jahresende", id="until-end-year-btn", variant="default")
            yield Label("Suche auch in \nBeschreibung:", classes="filter-label")
            yield Switch(value=self._search_description, id="search-desc-toggle")
            # yield Label("Suche:", classes="filter-label")
            yield Input(value=self.controls.search_text, placeholder="Suche nach...", id="search-input")

    def _normalize_label_refs(
        self, labels: Sequence[LabelReference | dict] | None
    ) -> list[LabelReference]:
        """Internal helper for `normalize_label_refs`."""
        refs: list[LabelReference] = []
        for label in labels or []:
            if isinstance(label, LabelReference):
                refs.append(label)
                continue
            if not isinstance(label, dict):
                continue
            try:
                label_id = int(label.get("id"))
            except (TypeError, ValueError):
                continue
            refs.append(
                LabelReference(
                    id=label_id,
                    name=str(label.get("name") or label_id),
                    color=label.get("color"),
                    assigned_count=int(label.get("assigned_count", 0) or 0),
                )
            )
        return refs

    def _iter_label_buttons(self) -> list[Button]:
        """Internal helper for `iter_label_buttons`."""
        return [self._create_label_button(ref) for ref in self.controls.visible_labels]

    def _create_label_button(self, label: LabelReference) -> Button:
        """Internal helper for `create_label_button`."""
        display = f"■ {label.name}"
        btn_id = f"label-{label.id}"
        classes = "label-toggle active" if label.id in self.controls.selected_label_ids else "label-toggle"
        return Button(display, id=btn_id, classes=classes)

    def update_labels(self, labels: Sequence[LabelReference | dict]) -> None:
        """Execute `update_labels`."""
        refs = self._normalize_label_refs(labels)
        self.controls.set_available_labels(refs)
        if self.is_attached:
            asyncio.create_task(self._swap_label_buttons())
        else:
            self.refresh()

    async def _swap_label_buttons(self) -> None:
        """Internal helper for `swap_label_buttons`."""
        try:
            container = self.query_one("#label-buttons", Horizontal)
        except Exception:
            return
        await container.remove_children("Button")
        await container.mount(*self._iter_label_buttons())

    @property
    def selected_label_ids(self) -> list[int]:
        """Execute `selected_label_ids`."""
        return list(self.controls.selected_label_ids)

    @property
    def start_date(self) -> str:
        """Execute `start_date`."""
        try:
            return self.query_one("#start-date", Input).value
        except Exception:
            return self.controls.start_date_text or self._default_start

    @property
    def end_date(self) -> str:
        """Execute `end_date`."""
        try:
            return self.query_one("#end-date", Input).value
        except Exception:
            return self.controls.end_date_text or self._default_end

    @property
    def search_in_description(self) -> bool:
        """Execute `search_in_description`."""
        return self.controls.search_in_description

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle the `input_changed` event callback."""
        if event.input.id == "search-input":
            self.search_text = event.value
            self.controls.search_text = event.value
            self.post_message(FilterChanged())
        elif event.input.id == "start-date":
            self.controls.start_date_text = event.value
        elif event.input.id == "end-date":
            self.controls.end_date_text = event.value

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle the `input_submitted` event callback."""
        if event.input.id in ("start-date", "end-date"):
            self.post_message(FilterChanged())

    def on_descendant_blur(self, event: DescendantBlur) -> None:
        """Handle the `descendant_blur` event callback."""
        widget = event.widget
        if isinstance(widget, Input) and widget.id in ("start-date", "end-date"):
            self.post_message(FilterChanged())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the `button_pressed` event callback."""
        btn_id = event.button.id or ""
        if btn_id == "until-end-year-btn":
            year = date.today().year
            month = date.today().month
            day = date.today().day
            start_val = f"{day:02d}.{month:02d}.{year}"
            end_val = f"31.12.{year}"
            self.query_one("#start-date", Input).value = start_val
            self.query_one("#end-date", Input).value = end_val
            self.controls.start_date_text = start_val
            self.controls.end_date_text = end_val
            self.post_message(FilterChanged())
            return
        if btn_id.startswith("label-"):
            try:
                label_id = int(btn_id.removeprefix("label-"))
            except ValueError:
                return
            self.toggle_label(label_id)
            if label_id in self.controls.selected_label_ids:
                event.button.add_class("active")
            else:
                event.button.remove_class("active")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle the `switch_changed` event callback."""
        if event.switch.id == "search-desc-toggle":
            self._search_description = bool(event.value)
            self.controls.search_in_description = self._search_description
            self.search_description_enabled = self._search_description
            self.post_message(FilterChanged())

    def toggle_label(self, label_id: int) -> None:
        """Execute `toggle_label`."""
        self.controls.toggle_label(label_id)
        self.post_message(FilterChanged())

    def set_focus_state(self, focused: bool) -> None:
        """Execute `set_focus_state`."""
        pass

    def focus_start_date(self) -> None:
        """Execute `focus_start_date`."""
        try:
            self.query_one("#start-date", Input).focus()
        except Exception:
            pass

    def focus_end_date(self) -> None:
        """Execute `focus_end_date`."""
        try:
            self.query_one("#end-date", Input).focus()
        except Exception:
            pass

    def focus_search(self) -> None:
        """Execute `focus_search`."""
        try:
            self.query_one("#search-input", Input).focus()
        except Exception:
            pass
