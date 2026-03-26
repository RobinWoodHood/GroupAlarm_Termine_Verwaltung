"""Main screen — horizontal split with filter/list and detail panel."""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Literal

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, LoadingIndicator, Static

from cli.widgets.filter_bar import FilterBar, FilterChanged
from cli.widgets.appointment_list import AppointmentList, AppointmentSelected
from cli.widgets.detail_panel import DetailPanel
from cli.widgets.confirmation_dialog import (
    ConfirmationDialog,
    UnsavedChangesDialog,
    RecurrenceStrategyDialog,
)
from cli.widgets.state import FilterControls, NavigationState, LabelReference
from framework.utils import DEFAULT_DISPLAY_TZ, format_de_datetime

logger = logging.getLogger(__name__)


class MainScreen(Screen):
    """Primary screen with list + detail split layout."""

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }
    #dry-run-banner {
        dock: top;
        height: 1;
        background: yellow;
        color: black;
        text-align: center;
        display: none;
    }
    #dry-run-banner.visible {
        display: block;
    }
    #loading-indicator {
        dock: top;
        height: 1;
        display: none;
    }
    #loading-indicator.visible {
        display: block;
    }
    #main-content {
        height: 1fr;
    }
    #left-pane {
        width: 3fr;
    }
    """

    BINDINGS = [
        ("left", "focus_list_panel", "List"),
        ("right", "focus_detail_panel", "Detail"),
        ("ctrl+f", "search", "Search"),
        ("ctrl+t", "focus_start_filter", "Zeitfilter"),
        ("e", "edit_mode", "Edit"),
        ("ctrl+s", "save", "Save"),
        ("escape", "cancel_edit", "Cancel"),
    ]

    def __init__(
        self,
        appointment_service,
        label_service,
        config=None,
        dry_run: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._appt_service = appointment_service
        self._label_service = label_service
        self._config = config
        self._dry_run = dry_run
        self._selected_appointment_id: int | None = None
        self._loading: bool = False
        self._active_start_date: date | None = None
        self._active_end_date: date | None = None
        initial_labels = self._build_label_directory()
        self._filter_controls = FilterControls(available_labels=initial_labels)
        if self._config and self._config.default_label_ids:
            self._filter_controls.selected_label_ids.update(self._config.default_label_ids)
        self.navigation_state = NavigationState()
        self._display_timezone = (
            self._config.timezone if self._config and self._config.timezone else DEFAULT_DISPLAY_TZ
        )

    def compose(self) -> ComposeResult:
        yield Static("⚠ DRY-RUN MODE — No changes will be saved to the server", id="dry-run-banner")
        yield LoadingIndicator(id="loading-indicator")
        with Horizontal(id="main-content"):
            with Vertical(id="left-pane"):
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
        if self._dry_run:
            banner = self.query_one("#dry-run-banner")
            banner.add_class("visible")
        # Provide label directory to detail panel for autocomplete/validation
        detail = self.query_one("#detail-panel", DetailPanel)
        detail.set_label_directory(self._build_label_directory())
        self._load_appointments()
        # Show empty-list hint if no appointments
        if not self._appt_service.appointments:
            detail.show_help()
        self._focus_list_panel()
        self._validate_display_timezone()

    def _load_appointments(self) -> None:
        try:
            self._appt_service.load()
        except Exception as exc:
            logger.error("Failed to load appointments: %s", exc)
            self.app.notify(f"Failed to load appointments: {exc}", severity="error")
            return
        self._update_filter_labels()
        self._active_start_date = None
        self._active_end_date = None
        appt_list = self.query_one("#appt-list", AppointmentList)
        appt_list.update_appointments(self._appt_service.appointments)

    def _validate_display_timezone(self) -> None:
        """Ensure the configured timezone is usable and warn when conversion falls back."""

        sample = datetime.now(timezone.utc)
        result = format_de_datetime(sample, tz_name=self._display_timezone)
        if result.warning:
            fallback_text = result.text
            message = (
                f"Zeitzone '{self._display_timezone}' konnte nicht geladen werden. "
                f"Rohwert: {fallback_text}"
            )
            self.app.notify(message, severity="warning")

    def _lock_ui(self) -> None:
        """Show loading indicator and block mutation actions."""
        self._loading = True
        self.query_one("#loading-indicator").add_class("visible")

    def _unlock_ui(self) -> None:
        """Hide loading indicator and re-enable mutation actions."""
        self._loading = False
        self.query_one("#loading-indicator").remove_class("visible")

    def _build_label_directory(self) -> list[LabelReference]:
        if self._label_service:
            return self._label_service.get_directory()
        return []

    def _filter_bar(self) -> FilterBar:
        return self.query_one("#filter-bar", FilterBar)

    def _focus_list_panel(self) -> None:
        try:
            table = self.query_one("#appt-table", DataTable)
        except Exception:
            return
        table.focus()
        self.navigation_state.set_active_panel("list", "#appt-table")
        self._filter_bar().set_focus_state(False)
        self._update_panel_focus_states("list")

    def _focus_detail_panel(self) -> None:
        detail = self.query_one("#detail-panel", DetailPanel)
        detail.focus_content()
        self.navigation_state.set_active_panel("detail", "#detail-panel")
        self._filter_bar().set_focus_state(False)
        self._update_panel_focus_states("detail")

    def _update_panel_focus_states(self, target: Literal["list", "detail", "filter"]) -> None:
        try:
            appt_list = self.query_one("#appt-list", AppointmentList)
            appt_list.set_focus_state(target == "list")
        except Exception:
            pass
        try:
            detail = self.query_one("#detail-panel", DetailPanel)
            detail.set_focus_state(target == "detail")
        except Exception:
            pass

    def on_filter_changed(self, event: FilterChanged) -> None:
        filter_bar = self.query_one("#filter-bar", FilterBar)
        search = filter_bar.search_text
        label_ids = filter_bar.selected_label_ids
        start_value = filter_bar.start_date
        end_value = filter_bar.end_date
        include_description = filter_bar.search_in_description

        start_ok, start_date, start_ready = self._parse_filter_date(start_value, "Start date")
        end_ok, end_date, end_ready = self._parse_filter_date(end_value, "End date")

        if not start_ok or not end_ok:
            return

        current_start = self._active_start_date
        current_end = self._active_end_date
        if start_ready:
            current_start = start_date
        if end_ready:
            current_end = end_date

        if (
            start_ready
            and end_ready
            and current_start is not None
            and current_end is not None
            and current_start > current_end
        ):
            self.app.notify("Start date must be before end date.", severity="warning")
            return

        self._appt_service.set_label_filter(label_ids if label_ids else None)
        self._appt_service.set_search(search, include_description)
        if start_ready or end_ready:
            self._appt_service.set_date_filter(current_start, current_end)

        reload_needed = False
        if start_ready and current_start != self._active_start_date:
            reload_needed = True
        if end_ready and current_end != self._active_end_date:
            reload_needed = True

        if reload_needed:
            if not self._reload_appointments(current_start, current_end):
                return

        appt_list = self.query_one("#appt-list", AppointmentList)
        appt_list.update_appointments(self._appt_service.appointments)

    def on_appointment_selected(self, event: AppointmentSelected) -> None:
        detail = self.query_one("#detail-panel", DetailPanel)
        # Check for unsaved changes before switching
        if detail.dirty:
            self._pending_selection_id = event.appointment_id
            self.app.push_screen(
                UnsavedChangesDialog(),
                self._handle_unsaved_on_selection,
            )
            return
        self._select_appointment(event.appointment_id)

    def _select_appointment(self, appt_id: int) -> None:
        self._selected_appointment_id = appt_id
        self.navigation_state.set_list_cursor(appt_id)
        appt = self._appt_service.get_by_id(appt_id)
        if appt:
            detail = self.query_one("#detail-panel", DetailPanel)
            display_tz = self._config.timezone if self._config else "Europe/Berlin"
            detail.show_appointment(appt, self._label_service, display_tz=display_tz)

    def _handle_unsaved_on_selection(self, result: str) -> None:
        if result == "save":
            self._do_save(then_select=getattr(self, "_pending_selection_id", None))
        elif result == "discard":
            detail = self.query_one("#detail-panel", DetailPanel)
            detail.discard_changes()
            pending = getattr(self, "_pending_selection_id", None)
            if pending:
                self._select_appointment(pending)
        # "cancel" — do nothing, stay on current

    def _parse_filter_date(self, value: str, field_name: str) -> tuple[bool, date | None, bool]:
        text = (value or "").strip()
        if not text:
            return True, None, True
        if text.count(".") < 2:
            # User is still typing; wait until full pattern is present
            return True, None, False

        normalized = self._normalize_date_text(text)
        if normalized is None:
            self.app.notify(f"{field_name} muss TT.MM.JJJJ sein.", severity="warning")
            return False, None, True

        try:
            parsed = datetime.strptime(normalized, "%d.%m.%Y").date()
        except ValueError:
            self.app.notify(f"{field_name} muss TT.MM.JJJJ sein.", severity="warning")
            return False, None, True
        return True, parsed, True

    def _normalize_date_text(self, text: str) -> str | None:
        parts = text.split(".")
        if len(parts) != 3 or not all(parts):
            return None
        day, month, year = parts
        if not (day.isdigit() and month.isdigit() and year.isdigit() and len(year) == 4):
            return None
        return f"{day.zfill(2)}.{month.zfill(2)}.{year}"

    def _reload_appointments(self, start_date: date | None, end_date: date | None) -> bool:
        start_dt = self._date_to_datetime(start_date)
        end_dt = self._date_to_datetime(end_date, clamp_end=True)
        try:
            self._appt_service.load(start_dt, end_dt)
        except Exception as exc:
            logger.error("Failed to load appointments: %s", exc)
            self.app.notify(f"Failed to load appointments: {exc}", severity="error")
            return False
        self._active_start_date = start_date
        self._active_end_date = end_date
        self._update_filter_labels()
        return True

    def _update_filter_labels(self) -> None:
        try:
            filter_bar = self.query_one("#filter-bar", FilterBar)
        except Exception:
            return
        directory = self._build_label_directory()
        counts = Counter()
        for appt in self._appt_service.appointments:
            for lid in appt.labelIDs or []:
                if isinstance(lid, int):
                    counts[lid] += 1
        enriched: list[LabelReference] = [
            LabelReference(
                id=label.id,
                name=label.name,
                color=label.color,
                assigned_count=count,
            )
            for label in directory
            if (count := counts.get(label.id, 0)) > 0
        ]
        filter_bar.update_labels(enriched)

    def _date_to_datetime(self, value: date | None, clamp_end: bool = False) -> datetime | None:
        if value is None:
            return None
        base = datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
        if clamp_end:
            return base + timedelta(days=1)
        return base

    # --- Edit Mode (US2) ---

    def action_edit_mode(self) -> None:
        if self._loading:
            return
        detail = self.query_one("#detail-panel", DetailPanel)
        if detail.current_appointment and not detail.edit_mode:
            detail.enter_edit_mode()
            # Activate detail panel so up/down navigates between inputs
            self.navigation_state.set_active_panel("detail", "#detail-panel")
            self._update_panel_focus_states("detail")

    def action_save(self) -> None:
        if self._loading:
            return
        detail = self.query_one("#detail-panel", DetailPanel)
        if not detail.edit_mode:
            return
        self._do_save()

    def _do_save(self, then_select: int | None = None) -> None:
        detail = self.query_one("#detail-panel", DetailPanel)
        appt = detail.current_appointment
        if not appt:
            return

        # Validate fields
        errors = detail.validate_fields()
        if errors:
            self.app.notify("\n".join(errors), severity="error")
            return

        if detail.create_mode:
            # Create flow
            values = {
                "name": appt.name,
                "description": appt.description,
                "startDate": appt.startDate.strftime("%Y-%m-%d %H:%M"),
                "endDate": appt.endDate.strftime("%Y-%m-%d %H:%M"),
                "organizationID": str(appt.organizationID),
                "labels": ",".join(str(lid) for lid in appt.labelIDs) if appt.labelIDs else "",
            }
            body = ConfirmationDialog.build_create_summary(values)
            dialog = ConfirmationDialog(
                title="Create New Appointment",
                body=body,
                confirm_label="Create",
            )
            self.app.push_screen(dialog, lambda ok: self._on_create_confirmed(ok, then_select))
        else:
            # Update flow
            old_values, new_values = detail.get_changes()
            if not old_values:
                self.app.notify("No changes to save.", severity="information")
                return
            label_warnings = detail.get_label_warnings()
            body = ConfirmationDialog.build_update_diff(
                old_values, new_values, warnings=label_warnings,
            )

            # Check for recurring appointment → ask strategy
            if appt.recurrence:
                self.app.push_screen(
                    RecurrenceStrategyDialog(),
                    lambda strategy: self._on_strategy_selected_for_update(strategy, old_values, new_values, then_select),
                )
            else:
                dialog = ConfirmationDialog(
                    title="Confirm Update",
                    body=body,
                )
                self.app.push_screen(dialog, lambda ok: self._on_update_confirmed(ok, "all", then_select))

    def _on_strategy_selected_for_update(self, strategy: str, old_values: dict, new_values: dict, then_select: int | None) -> None:
        if not strategy:
            return  # cancelled
        detail = self.query_one("#detail-panel", DetailPanel)
        label_warnings = detail.get_label_warnings()
        body = ConfirmationDialog.build_update_diff(
            old_values, new_values, warnings=label_warnings,
        )
        dialog = ConfirmationDialog(
            title=f"Confirm Update ({strategy})",
            body=body,
        )
        self.app.push_screen(dialog, lambda ok: self._on_update_confirmed(ok, strategy, then_select))

    def _on_update_confirmed(self, confirmed: bool, strategy: str, then_select: int | None) -> None:
        if not confirmed:
            return
        detail = self.query_one("#detail-panel", DetailPanel)
        appt = detail.current_appointment
        if not appt:
            return

        reselect_id = appt.id or then_select
        self._lock_ui()
        try:
            self._appt_service.update(appt, strategy=strategy)
            self.app.notify("Appointment updated successfully.", severity="information")
            detail.discard_changes()
            self._load_appointments()
            if reselect_id:
                self._select_appointment(reselect_id)
        except Exception as exc:
            logger.error("Failed to update appointment: %s", exc)
            self.app.notify(f"Update failed: {exc}", severity="error")
        finally:
            self._unlock_ui()

    def _on_create_confirmed(self, confirmed: bool, then_select: int | None) -> None:
        if not confirmed:
            return
        detail = self.query_one("#detail-panel", DetailPanel)
        appt = detail.current_appointment
        if not appt:
            return

        self._lock_ui()
        try:
            self._appt_service.create(appt)
            self.app.notify("Appointment created successfully.", severity="information")
            detail.discard_changes()
            detail.show_help()
            self._load_appointments()
        except Exception as exc:
            logger.error("Failed to create appointment: %s", exc)
            self.app.notify(f"Create failed: {exc}", severity="error")
        finally:
            self._unlock_ui()

    def action_cancel_edit(self) -> None:
        detail = self.query_one("#detail-panel", DetailPanel)
        if detail.edit_mode:
            if detail.dirty:
                self.app.push_screen(
                    UnsavedChangesDialog(),
                    self._handle_unsaved_on_cancel,
                )
            else:
                detail.discard_changes()

    def _handle_unsaved_on_cancel(self, result: str) -> None:
        if result == "save":
            self._do_save()
        elif result == "discard":
            detail = self.query_one("#detail-panel", DetailPanel)
            detail.discard_changes()
        # "cancel" — stay in edit mode

    # --- New Appointment (US4) ---

    def action_new_appointment(self) -> None:
        if self._loading:
            return
        detail = self.query_one("#detail-panel", DetailPanel)
        if detail.dirty:
            self.app.push_screen(
                UnsavedChangesDialog(),
                lambda result: self._handle_unsaved_then_new(result),
            )
            return
        self._start_create()

    def _handle_unsaved_then_new(self, result: str) -> None:
        if result == "save":
            self._do_save()
        elif result == "discard":
            detail = self.query_one("#detail-panel", DetailPanel)
            detail.discard_changes()
            self._start_create()

    def _start_create(self) -> None:
        detail = self.query_one("#detail-panel", DetailPanel)
        defaults = {
            "organization_id": self._appt_service._organization_id,
            "timezone": "Europe/Berlin",
            "duration_hours": 4,
        }
        if self._config:
            defaults["timezone"] = self._config.timezone
            defaults["duration_hours"] = self._config.default_appointment_duration_hours
        detail.enter_create_mode(defaults)

    # --- Delete Appointment (US5) ---

    def action_delete_appointment(self) -> None:
        if self._loading:
            return
        if not self._selected_appointment_id:
            self.app.notify("No appointment selected.", severity="warning")
            return
        appt = self._appt_service.get_by_id(self._selected_appointment_id)
        if not appt:
            self.app.notify("Appointment not found.", severity="error")
            return

        if appt.recurrence:
            self.app.push_screen(
                RecurrenceStrategyDialog(),
                lambda strategy: self._on_delete_strategy(strategy, appt),
            )
        else:
            self._show_delete_confirmation(appt, "all")

    def _on_delete_strategy(self, strategy: str, appt) -> None:
        if not strategy:
            return  # cancelled
        self._show_delete_confirmation(appt, strategy)

    def _show_delete_confirmation(self, appt, strategy: str) -> None:
        body = ConfirmationDialog.build_delete_summary(
            appt.name,
            appt.startDate.strftime("%Y-%m-%d %H:%M"),
            appt.endDate.strftime("%Y-%m-%d %H:%M"),
        )
        dialog = ConfirmationDialog(
            title="Delete Appointment",
            body=body,
            warning="⚠ This action cannot be undone!",
            confirm_label="Delete",
        )
        self.app.push_screen(dialog, lambda ok: self._on_delete_confirmed(ok, appt, strategy))

    def _on_delete_confirmed(self, confirmed: bool, appt, strategy: str) -> None:
        if not confirmed:
            return
        self._lock_ui()
        try:
            time_param = appt.startDate.isoformat() if strategy in ("single", "upcoming") else None
            self._appt_service.delete(appt.id, strategy=strategy, time_=time_param)
            self.app.notify("Appointment deleted.", severity="information")
            detail = self.query_one("#detail-panel", DetailPanel)
            detail.show_help()
            self._selected_appointment_id = None
            self._load_appointments()
        except Exception as exc:
            logger.error("Failed to delete appointment: %s", exc)
            self.app.notify(f"Delete failed: {exc}", severity="error")
        finally:
            self._unlock_ui()

    # --- Export (US3) ---

    def action_export(self) -> None:
        if self._loading:
            return
        appointments = self._appt_service.appointments
        if not appointments:
            self.app.notify("No appointments to export.", severity="warning")
            return

        from framework.exporter import export_appointments

        default_name = f"appointments_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        output_path = Path(default_name)

        # Handle file exists
        if output_path.exists():
            counter = 1
            while output_path.exists():
                output_path = Path(f"appointments_{datetime.now().strftime('%Y-%m-%d')}_{counter}.xlsx")
                counter += 1

        try:
            tz = "Europe/Berlin"
            if self._config:
                tz = self._config.timezone
            export_appointments(appointments, output_path, timezone=tz)
            self.app.notify(f"Exported {len(appointments)} appointments to {output_path}", severity="information")
        except Exception as exc:
            logger.error("Export failed: %s", exc)
            self.app.notify(f"Export failed: {exc}", severity="error")

    # --- Navigation & Filter ---

    def action_search(self) -> None:
        filter_bar = self.query_one("#filter-bar", FilterBar)
        self.navigation_state.set_active_panel("filter", "#search-input")
        filter_bar.focus_search()
        self._update_panel_focus_states("filter")

    def action_focus_start_filter(self) -> None:
        filter_bar = self.query_one("#filter-bar", FilterBar)
        self.navigation_state.set_active_panel("filter", "#start-date")
        filter_bar.focus_start_date()
        self._update_panel_focus_states("filter")

    def action_focus_list_panel(self) -> None:
        self._focus_list_panel()

    def action_focus_detail_panel(self) -> None:
        self._focus_detail_panel()

    def action_toggle_sort(self) -> None:
        self._appt_service.toggle_sort()
        appt_list = self.query_one("#appt-list", AppointmentList)
        appt_list.update_appointments(self._appt_service.appointments)

    def action_refresh(self) -> None:
        self._load_appointments()

    def refresh_list(self) -> None:
        self._load_appointments()

    def _check_dirty_before_quit(self) -> None:
        """Check for unsaved changes before quitting."""
        detail = self.query_one("#detail-panel", DetailPanel)
        if detail.dirty:
            self.app.push_screen(
                UnsavedChangesDialog(),
                self._handle_unsaved_on_quit,
            )
        else:
            self.app.exit()

    def _handle_unsaved_on_quit(self, result: str) -> None:
        if result == "save":
            self._do_save()
            self.app.exit()
        elif result == "discard":
            self.app.exit()
        # "cancel" — stay
