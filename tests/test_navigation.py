import pytest

from cli.widgets.state import FilterControls, LabelReference, NavigationState


def _make_labels(count: int = 7):
    return [LabelReference(id=i, name=f"Label {i}") for i in range(1, count + 1)]


def test_navigation_state_switches_active_panel():
    state = NavigationState()
    assert state.active_panel == "list"

    state.set_active_panel("detail")
    assert state.active_panel == "detail"

    state.set_active_panel("filter", focused_widget_id="#search-input")
    assert state.active_panel == "filter"
    assert state.focused_widget_id == "#search-input"

    with pytest.raises(ValueError):
        state.set_active_panel("invalid")


def test_navigation_state_tracks_cursor_and_filter_focus():
    state = NavigationState()
    state.set_list_cursor(42)
    assert state.list_cursor_key == 42

    state.advance_filter_focus()
    state.advance_filter_focus()
    assert state.filter_focus_index == 2

    state.reset_filter_focus()
    assert state.filter_focus_index == 0


def test_filter_controls_preview_and_expansion():
    controls = FilterControls(available_labels=_make_labels())
    # all labels are always visible (no preview limit)
    assert len(controls.visible_labels) == 7


def test_filter_controls_toggle_selection_and_cleanup():
    controls = FilterControls(available_labels=_make_labels(3))
    controls.expand_labels()

    controls.toggle_label(1)
    controls.toggle_label(2)
    assert controls.selected_label_ids == {1, 2}

    controls.toggle_label(2)
    assert controls.selected_label_ids == {1}

    # Unknown label IDs are ignored
    controls.toggle_label(999)
    assert controls.selected_label_ids == {1}


def test_filter_controls_tracks_shortcut_expansion():
    controls = FilterControls(available_labels=_make_labels())
    controls.register_shortcut_focus("#start-date")
    assert controls.preview_mode is False
    assert controls.focus_history[-1] == "#start-date"
