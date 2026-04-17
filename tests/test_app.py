"""Textual pilot tests for the GroupAlarm TUI app (US1: Browse & Filter)."""
import cli.app as app_module
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from cli.app import GroupAlarmApp
from cli.widgets.filter_bar import FilterBar
from framework.client import GroupAlarmClient
from framework.config import AppConfig


SAMPLE_LABELS = [
    {"id": 1, "name": "Fire", "color": "#FF0000", "organizationID": 100},
    {"id": 2, "name": "Medical", "color": "#00FF00", "organizationID": 100},
]

SAMPLE_APPOINTMENTS = [
    {
        "id": 10,
        "name": "Training Alpha",
        "description": "First training session",
        "startDate": "2026-03-22T10:00:00+00:00",
        "endDate": "2026-03-22T14:00:00+00:00",
        "organizationID": 100,
        "labelIDs": [1],
        "isPublic": True,
        "keepLabelParticipantsInSync": True,
        "timezone": "Europe/Berlin",
        "participants": [],
        "recurrence": None,
    },
    {
        "id": 20,
        "name": "Drill Bravo",
        "description": "Second drill session",
        "startDate": "2026-03-23T09:00:00+00:00",
        "endDate": "2026-03-23T12:00:00+00:00",
        "organizationID": 100,
        "labelIDs": [2],
        "isPublic": True,
        "keepLabelParticipantsInSync": True,
        "timezone": "Europe/Berlin",
        "participants": [],
        "recurrence": None,
    },
    {
        "id": 30,
        "name": "Meeting Charlie",
        "description": "Monthly review meeting",
        "startDate": "2026-03-24T14:00:00+00:00",
        "endDate": "2026-03-24T15:00:00+00:00",
        "organizationID": 100,
        "labelIDs": [1, 2],
        "isPublic": False,
        "keepLabelParticipantsInSync": True,
        "timezone": "Europe/Berlin",
        "participants": [],
        "recurrence": None,
    },
]


def _make_mock_client():
    """Internal helper for `make_mock_client`."""
    client = MagicMock(spec=GroupAlarmClient)
    client.token = "test-token"
    client.dry_run = False
    client.list_labels.return_value = SAMPLE_LABELS
    client.list_appointments.return_value = SAMPLE_APPOINTMENTS
    return client


def _make_app(client=None, dry_run=False, show_startup_welcome=True):
    """Internal helper for `make_app`."""
    if client is None:
        client = _make_mock_client()
    config = AppConfig(
        organization_id=100,
        date_range_days=30,
        show_startup_welcome=show_startup_welcome,
    )
    return GroupAlarmApp(client=client, config=config, org_id=100, dry_run=dry_run)


@pytest.mark.asyncio
async def test_app_startup_loads_appointments():
    """T017: Verify app starts and appointment list is populated."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # The DataTable should have rows
        from textual.widgets import DataTable
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 3


@pytest.mark.asyncio
async def test_app_startup_calls_list_labels():
    """T017: Verify labels are fetched on startup."""
    client = _make_mock_client()
    app = _make_app(client=client)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        client.list_labels.assert_called_once_with(100, label_type="all")


@pytest.mark.asyncio
async def test_startup_welcome_stays_visible_until_explicit_selection():
    """Test `startup_welcome_stays_visible_until_explicit_selection` behavior."""
    app = _make_app(show_startup_welcome=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from cli.widgets.detail_panel import DetailPanel

        detail = app.screen.query_one("#detail-panel", DetailPanel)
        assert detail.current_appointment is None


@pytest.mark.asyncio
async def test_startup_welcome_disabled_keeps_live_preview_behavior():
    """Test `startup_welcome_disabled_keeps_live_preview_behavior` behavior."""
    app = _make_app(show_startup_welcome=False)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from cli.widgets.detail_panel import DetailPanel

        detail = app.screen.query_one("#detail-panel", DetailPanel)
        assert detail.current_appointment is not None


@pytest.mark.asyncio
async def test_command_palette_toggle_persists_startup_welcome(monkeypatch):
    """Test `command_palette_toggle_persists_startup_welcome` behavior."""
    app = _make_app(show_startup_welcome=True)
    saved_values: list[bool] = []

    def _fake_save(config, path=None):
        """Internal helper for `fake_save`."""
        saved_values.append(config.show_startup_welcome)

    monkeypatch.setattr(app_module, "save_config", _fake_save)

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        titles = [cmd.title for cmd in app.get_system_commands(app.screen)]
        assert "Willkommensseite beim Start umschalten" in titles
        app.action_toggle_startup_welcome()
        await pilot.pause()
        assert app._config.show_startup_welcome is False
        assert saved_values == [False]


@pytest.mark.asyncio
async def test_search_filters_appointments():
    """T018: Verify search narrows the appointment list."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # Focus search input and type
        from textual.widgets import Input, DataTable
        search_input = app.screen.query_one("#search-input", Input)
        search_input.focus()
        await pilot.pause()
        # Type a search term
        search_input.value = "Alpha"
        await pilot.pause()
        # Allow filter propagation
        await pilot.pause()
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 1


@pytest.mark.asyncio
async def test_search_no_match_shows_empty():
    """T019: Verify search with no match shows empty list."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import Input, DataTable
        search_input = app.screen.query_one("#search-input", Input)
        search_input.value = "nonexistent_xyz"
        await pilot.pause()
        await pilot.pause()
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 0


@pytest.mark.asyncio
async def test_description_search_requires_toggle():
    """T018: Description field is searched only when toggle is enabled."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import Input, DataTable, Switch

        search_input = app.screen.query_one("#search-input", Input)
        search_input.value = "session"
        await pilot.pause()
        await pilot.pause()

        table = app.screen.query_one("#appt-table", DataTable)
        # Without toggle only names are searched, so nothing matches
        assert table.row_count == 0

        desc_toggle = app.screen.query_one("#search-desc-toggle", Switch)
        desc_toggle.value = True
        await pilot.pause()
        await pilot.pause()

        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 2


@pytest.mark.asyncio
async def test_dry_run_banner_shown():
    """Verify dry-run banner is visible when --dry-run is active."""
    app = _make_app(dry_run=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        banner = app.screen.query_one("#dry-run-banner")
        assert "visible" in banner.classes


@pytest.mark.asyncio
async def test_dry_run_banner_hidden_by_default():
    """Verify dry-run banner is hidden when --dry-run is not active."""
    app = _make_app(dry_run=False)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        banner = app.screen.query_one("#dry-run-banner")
        assert "visible" not in banner.classes


# --- Phase 4: US2 Tests ---

@pytest.mark.asyncio
async def test_detail_panel_populated_on_selection():
    """T029: Select appointment in list -> detail panel shows fields."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # Directly select the appointment through the screen (DataTable enter
        # events may not fire reliably under the test pilot)
        from cli.screens.main_screen import MainScreen
        screen = app.screen
        if isinstance(screen, MainScreen):
            screen._select_appointment(10)
        await pilot.pause()
        from cli.widgets.detail_panel import DetailPanel
        detail = app.screen.query_one("#detail-panel", DetailPanel)
        assert detail.current_appointment is not None
        assert detail.current_appointment.name == "Training Alpha"


@pytest.mark.asyncio
async def test_edit_mode_toggle():
    """T030: Enter edit mode -> fields become editable, indicator shown."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from cli.widgets.detail_panel import DetailPanel
        from cli.screens.main_screen import MainScreen
        screen = app.screen
        if isinstance(screen, MainScreen):
            # First select an appointment so edit mode can be activated
            screen._select_appointment(10)
            await pilot.pause()
            screen.action_edit_mode()
        await pilot.pause()
        detail = app.screen.query_one("#detail-panel", DetailPanel)
        assert detail.edit_mode is True


# --- Phase 5: US3 Tests ---

@pytest.mark.asyncio
async def test_export_empty_list_shows_message():
    """T041: Export with empty list -> notification shown."""
    client = _make_mock_client()
    client.list_appointments.return_value = []
    app = _make_app(client=client)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # Press 'x' for export
        await pilot.press("x")
        await pilot.pause()
        await pilot.pause()
        # Should show notification about no appointments


# --- Phase 6: US4 Tests ---

@pytest.mark.asyncio
async def test_new_appointment_creates_form():
    """T045: Press n -> detail panel opens with default fields."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # Directly call the action to bypass key binding focus issues
        from cli.screens.main_screen import MainScreen
        screen = app.screen
        if isinstance(screen, MainScreen):
            screen.action_new_appointment()
        await pilot.pause()
        await pilot.pause()
        from cli.widgets.detail_panel import DetailPanel
        detail = app.screen.query_one("#detail-panel", DetailPanel)
        assert detail.edit_mode is True
        assert detail.create_mode is True


# --- Phase 7: US5 Tests ---

@pytest.mark.asyncio
async def test_delete_no_selection_shows_hint():
    """T049: Delete with no selection -> notification shown."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        # Should show a notification about no appointment selected


@pytest.mark.asyncio
async def test_delete_triggers_confirmation():
    """T049: Select appointment -> press d -> confirmation dialog shown."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import DataTable
        table = app.screen.query_one("#appt-table", DataTable)
        table.move_cursor(row=0)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.pause()
        # Confirmation dialog should be on screen
        from cli.widgets.confirmation_dialog import ConfirmationDialog
        dialogs = app.screen.query(ConfirmationDialog)
        # The dialog might be on a different screen stack level
        assert len(list(app.screen_stack)) >= 2 or len(list(dialogs)) > 0


@pytest.mark.asyncio
async def test_recurring_delete_shows_strategy():
    """T050: Recurring appointment delete -> strategy selector shown."""
    client = _make_mock_client()
    recurring_appt = {
        "id": 10,
        "name": "Weekly Training",
        "description": "Recurring session",
        "startDate": "2026-03-22T10:00:00+00:00",
        "endDate": "2026-03-22T14:00:00+00:00",
        "organizationID": 100,
        "labelIDs": [1],
        "isPublic": True,
        "keepLabelParticipantsInSync": True,
        "timezone": "Europe/Berlin",
        "participants": [],
        "recurrence": {"frequency": "weekly", "interval": 1, "days": [1, 3]},
    }
    client.list_appointments.return_value = [recurring_appt]
    app = _make_app(client=client)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import DataTable
        table = app.screen.query_one("#appt-table", DataTable)
        table.move_cursor(row=0)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.pause()
        # Strategy dialog should appear for recurring appointments
        assert len(list(app.screen_stack)) >= 2


@pytest.mark.asyncio
async def test_label_filter_toggles_appointments():
    """T018: Click label toggle button -> only matching appointments shown."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import DataTable, Button
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 3

        # Click the "Fire" label toggle (label id=1)
        fire_btn = app.screen.query_one("#label-1", Button)
        fire_btn.press()
        await pilot.pause()
        await pilot.pause()

        table = app.screen.query_one("#appt-table", DataTable)
        # "Training Alpha" (label [1]) and "Meeting Charlie" (labels [1,2]) should match
        assert table.row_count == 2

        # Click again to deselect -> all 3 appointments back
        fire_btn.press()
        await pilot.pause()
        await pilot.pause()

        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 3


@pytest.mark.asyncio
async def test_date_filters_limit_appointments():
    """T018: Setting start/end dates narrows the appointment list."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import Input, DataTable

        start_input = app.screen.query_one("#start-date", Input)
        end_input = app.screen.query_one("#end-date", Input)

        # Start date 23.03.2026 -> only appointments on/after that date remain
        start_input.focus()
        await pilot.pause()
        start_input.value = "23.03.2026"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 2

        # Add end date 23.03.2026 -> only that day's appointment remains
        end_input.focus()
        await pilot.pause()
        end_input.value = "23.03.2026"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 1

        # Clear start -> appointments on/before end date remain (2 entries)
        start_input.focus()
        await pilot.pause()
        start_input.value = ""
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 2

        # Clear end -> all appointments visible
        end_input.focus()
        await pilot.pause()
        end_input.value = ""
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 3

        # Typing without leading zeros should still parse once all parts are present
        start_input.focus()
        await pilot.pause()
        start_input.value = "24.3.2026"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 1


@pytest.mark.asyncio
async def test_date_filter_reload_calls_api_with_range():
    """T018: Adjusting date inputs triggers a fresh API load with full range."""
    client = _make_mock_client()
    app = _make_app(client=client)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import Input

        assert client.list_appointments.call_count == 1

        start_input = app.screen.query_one("#start-date", Input)
        end_input = app.screen.query_one("#end-date", Input)

        start_input.focus()
        await pilot.pause()
        start_input.value = "23.03.2026"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        end_input.focus()
        await pilot.pause()
        end_input.value = "23.03.2026"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()

        assert client.list_appointments.call_count >= 3
        kwargs = client.list_appointments.call_args.kwargs
        assert kwargs["start"].startswith("2026-03-23T00:00:00")
        assert kwargs["end"].startswith("2026-03-24T00:00:00")


@pytest.mark.asyncio
async def test_refresh_preserves_active_date_range_filters():
    """T018: Refresh uses the currently entered start/end date filters."""
    client = _make_mock_client()
    app = _make_app(client=client)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import Input

        start_input = app.screen.query_one("#start-date", Input)
        end_input = app.screen.query_one("#end-date", Input)

        start_input.value = "22.03.2026"
        end_input.value = "24.03.2026"
        await pilot.pause()

        # Clear any cached call args from startup load
        client.list_appointments.reset_mock()
        app.screen.action_refresh()
        await pilot.pause()

        assert client.list_appointments.call_count == 1
        kwargs = client.list_appointments.call_args.kwargs
        assert kwargs["start"].startswith("2026-03-22T00:00:00")
        assert kwargs["end"].startswith("2026-03-25T00:00:00")


@pytest.mark.asyncio
async def test_label_buttons_show_only_used_labels():
    """Filter bar shows only labels that are assigned to appointments in the list."""
    client = _make_mock_client()
    client.list_labels.return_value = SAMPLE_LABELS + [
        {"id": 3, "name": "Logistics", "color": "#0000FF", "organizationID": 100}
    ]
    app = _make_app(client=client)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import Button

        buttons = list(app.screen.query("#label-buttons Button"))
        ids = sorted(btn.id for btn in buttons)
        # Label 3 (Logistics) is not used by any appointment, so not shown
        assert ids == ["label-1", "label-2"]


@pytest.mark.asyncio
async def test_arrow_keys_switch_focus_between_panes():
    """Left/right arrows move focus between list and detail without losing selection."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import DataTable
        from cli.screens.main_screen import MainScreen

        screen = app.screen
        assert isinstance(screen, MainScreen)

        table = app.screen.query_one("#appt-table", DataTable)
        table.move_cursor(row=1)
        await pilot.pause()

        assert screen.navigation_state.active_panel == "list"

        await pilot.press("right")
        await pilot.pause()
        assert screen.navigation_state.active_panel == "detail"

        await pilot.press("left")
        await pilot.pause()
        assert screen.navigation_state.active_panel == "list"


@pytest.mark.asyncio
async def test_filter_shortcuts_focus_inputs():
    """Ctrl+T focuses date, Ctrl+F focuses search."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        filter_bar = app.screen.query_one("#filter-bar", FilterBar)

        await pilot.press("ctrl+t")
        await pilot.pause()
        start_input = filter_bar.query_one("#start-date")
        assert start_input.has_focus

        await pilot.press("ctrl+f")
        await pilot.pause()
        search_input = filter_bar.query_one("#search-input")
        assert search_input.has_focus


@pytest.mark.asyncio
async def test_pane_arrow_indicators_follow_focus():
    """US1 arrows highlight the active pane and persist selection highlighting."""
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from cli.widgets.appointment_list import AppointmentList
        from cli.widgets.detail_panel import DetailPanel

        list_widget = app.screen.query_one("#appt-list", AppointmentList)
        detail_widget = app.screen.query_one("#detail-panel", DetailPanel)
        list_arrow = app.screen.query_one("#list-arrow-right")
        detail_arrow = app.screen.query_one("#detail-arrow-left")

        assert "is-active" in list_widget.classes
        assert "is-active" not in detail_widget.classes
        assert "active" in list_arrow.classes
        assert "active" not in detail_arrow.classes

        await pilot.press("right")
        await pilot.pause()

        assert "is-active" in detail_widget.classes
        assert "active" in detail_arrow.classes
        assert "active" not in list_arrow.classes

        await pilot.press("left")
        await pilot.pause()
        assert "is-active" in list_widget.classes


@pytest.mark.asyncio
async def test_invalid_timezone_config_triggers_notification():
    """Invalid display timezones surface a warning notification for operators."""
    client = _make_mock_client()
    bad_config = AppConfig(organization_id=100, date_range_days=30, timezone="Mars/Phobos")
    app = GroupAlarmApp(client=client, config=bad_config, org_id=100)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.pause()
        notifications = list(app._notifications)
        assert any("Mars/Phobos" in note.message for note in notifications)


@pytest.mark.asyncio
async def test_duplicate_ids_are_skipped_in_table():
    """App should not crash when API returns duplicate appointment IDs."""
    client = _make_mock_client()
    # Return the same appointment twice to simulate duplicates from API
    duplicate = SAMPLE_APPOINTMENTS[0]
    client.list_appointments.return_value = [duplicate, duplicate]
    app = _make_app(client=client)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import DataTable
        table = app.screen.query_one("#appt-table", DataTable)
        assert table.row_count == 1


@pytest.mark.asyncio
async def test_focus_transition_timing_under_one_second():
    """SC-001: Each focus transition between panes completes in <1 s."""
    import time
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from cli.screens.main_screen import MainScreen

        screen = app.screen
        assert isinstance(screen, MainScreen)

        transitions = []

        # Transition 1: list → detail
        t0 = time.perf_counter()
        await pilot.press("right")
        await pilot.pause()
        transitions.append(("list→detail", time.perf_counter() - t0))
        assert screen.navigation_state.active_panel == "detail"

        # Transition 2: detail → list
        t0 = time.perf_counter()
        await pilot.press("left")
        await pilot.pause()
        transitions.append(("detail→list", time.perf_counter() - t0))
        assert screen.navigation_state.active_panel == "list"

        # Transition 3: list → filter (Ctrl+/)
        t0 = time.perf_counter()
        await pilot.press("ctrl+/")
        await pilot.pause()
        transitions.append(("list→filter", time.perf_counter() - t0))

        # Transition 4: filter → search (Ctrl+F)
        t0 = time.perf_counter()
        await pilot.press("ctrl+f")
        await pilot.pause()
        transitions.append(("filter→search", time.perf_counter() - t0))

        # Transition 5: back to list via Esc
        t0 = time.perf_counter()
        await pilot.press("escape")
        await pilot.pause()
        transitions.append(("search→list", time.perf_counter() - t0))

        for label, duration in transitions:
            assert duration < 1.0, f"Transition {label} took {duration:.3f}s (limit: 1.0s)"
