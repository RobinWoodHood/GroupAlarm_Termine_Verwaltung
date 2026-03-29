"""GroupAlarm TUI application — Textual App subclass."""
from __future__ import annotations

import logging
from typing import Iterable, Optional

from textual.app import App, SystemCommand
from textual.binding import Binding

from framework.client import GroupAlarmClient
from framework.config import AppConfig, save_config
from cli.services.label_service import LabelService
from cli.services.appointment_service import AppointmentService
from cli.services.user_service import UserService
from cli.screens.main_screen import MainScreen

logger = logging.getLogger(__name__)


class GroupAlarmApp(App):
    """Interactive TUI for GroupAlarm appointment management."""

    TITLE = "GroupAlarm TUI"
    CSS_PATH = "../cli/styles/app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+f", "search", "Search", show=True, priority=True),
        Binding("ctrl+t", "focus_start_filter", "Zeitfilter", show=True, priority=True),
        Binding("ctrl+o", "import", "Import", show=True),
        Binding("ctrl+p", "command_palette", "Command Palette", show=False),
        Binding("n", "new_appointment", "New", show=True),
        Binding("d", "delete_appointment", "Delete", show=True),
        Binding("x", "export", "Export", show=True),
        Binding("i", "add_importer_tokens", "Add Tokens", show=True),
        Binding("f1", "help", "Help", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(
        self,
        client: GroupAlarmClient,
        config: AppConfig,
        org_id: Optional[int] = None,
        dry_run: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._client = client
        self._config = config
        self._org_id = org_id
        self._dry_run = dry_run
        self._label_service: Optional[LabelService] = None
        self._user_service: Optional[UserService] = None
        self._appt_service: Optional[AppointmentService] = None

    def on_mount(self) -> None:
        # Ensure we have an org ID
        if not self._org_id:
            self._org_id = self._config.organization_id

        if not self._org_id:
            self.notify("Organization ID not configured. Please set it in .groupalarm.toml or use --org-id.", severity="error")
            self.exit(return_code=1)
            return

        # Initialize services
        self._label_service = LabelService(self._client, self._org_id)
        try:
            self._label_service.load()
        except Exception as exc:
            logger.warning("Failed to load labels: %s", exc)

        self._user_service = UserService(self._client, self._org_id)
        self._user_service.load()

        # Validate default_label_ids against fetched labels
        if self._config.default_label_ids and self._label_service:
            valid_ids = {label["id"] for label in self._label_service.labels}
            invalid = [lid for lid in self._config.default_label_ids if lid not in valid_ids]
            if invalid:
                logger.warning("Invalid default_label_ids in config (not found in API): %s", invalid)

        self._appt_service = AppointmentService(
            self._client,
            self._org_id,
            date_range_days=self._config.date_range_days,
        )

        self.push_screen(
            MainScreen(
                appointment_service=self._appt_service,
                label_service=self._label_service,
                user_service=self._user_service,
                config=self._config,
                dry_run=self._dry_run,
            )
        )

    def get_system_commands(self, screen) -> Iterable[SystemCommand]:
        """Expose custom commands in Ctrl+P command palette."""
        yield from super().get_system_commands(screen)
        state = "aktiviert" if self._config.show_startup_welcome else "deaktiviert"
        yield SystemCommand(
            "Willkommensseite beim Start umschalten",
            f"Aktuell: {state}. Speichert in .groupalarm.toml.",
            self.action_toggle_startup_welcome,
            discover=True,
        )

    def action_toggle_startup_welcome(self) -> None:
        """Toggle startup welcome behavior and persist config."""
        self._config.show_startup_welcome = not self._config.show_startup_welcome
        try:
            save_config(self._config)
        except Exception as exc:
            logger.error("Failed to persist startup welcome toggle: %s", exc)
            self.notify(f"Konnte Config nicht speichern: {exc}", severity="error")
            return

        state = "aktiviert" if self._config.show_startup_welcome else "deaktiviert"
        self.notify(
            f"Willkommensseite beim Start: {state} (gilt beim naechsten Start).",
            severity="information",
        )

    def action_focus_start_filter(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_focus_start_filter"):
            screen.action_focus_start_filter()

    def action_search(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_search"):
            screen.action_search()

    def action_new_appointment(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_new_appointment"):
            screen.action_new_appointment()

    def action_delete_appointment(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_delete_appointment"):
            screen.action_delete_appointment()

    def action_export(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_export"):
            screen.action_export()

    def action_add_importer_tokens(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_add_importer_tokens"):
            screen.action_add_importer_tokens()

    def action_import(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_import"):
            screen.action_import()

    def action_help(self) -> None:
        from cli.screens.help_screen import HelpScreen
        self.push_screen(HelpScreen())

    def action_refresh(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_refresh"):
            screen.action_refresh()

    def action_quit(self) -> None:
        """Quit with unsaved changes guard."""
        screen = self.screen
        if hasattr(screen, "_check_dirty_before_quit"):
            screen._check_dirty_before_quit()
        else:
            self.exit()
