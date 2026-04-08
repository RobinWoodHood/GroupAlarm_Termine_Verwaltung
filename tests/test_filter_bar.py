import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from cli.widgets.filter_bar import FilterBar
from cli.widgets.state import FilterControls, LabelReference


def _make_labels(count: int, zero_ids=None):
    """Internal helper for `make_labels`."""
    zero_ids = zero_ids or set()
    return [
        LabelReference(
            id=i,
            name=f"Label {i}",
            color="#00AEEF",
            assigned_count=0 if i in zero_ids else i,
        )
        for i in range(1, count + 1)
    ]


class _FilterBarTestApp(App):
    """Container class `_FilterBarTestApp`."""
    def __init__(self, widget: FilterBar):
        """Initialize the _FilterBarTestApp instance."""
        super().__init__()
        self._widget = widget

    def compose(self) -> ComposeResult:
        """Execute `compose`."""
        yield self._widget
        yield Static(id="sentinel")


@pytest.mark.asyncio
async def test_filter_bar_shows_all_labels():
    """Test `filter_bar_shows_all_labels` behavior."""
    controls = FilterControls()
    labels = _make_labels(7)
    fb = FilterBar(labels=labels, controls=controls)

    app = _FilterBarTestApp(fb)
    async with app.run_test(size=(120, 20)) as pilot:
        await pilot.pause()
        buttons = list(fb.query("#label-buttons Button"))
        assert len(buttons) == 7  # all labels shown, no preview limit


@pytest.mark.asyncio
async def test_zero_match_labels_show_indicator():
    """Test `zero_match_labels_show_indicator` behavior."""
    controls = FilterControls()
    labels = _make_labels(3, zero_ids={2})
    fb = FilterBar(labels=labels, controls=controls)

    app = _FilterBarTestApp(fb)
    async with app.run_test(size=(120, 20)) as pilot:
        await pilot.pause()
        zero_button = fb.query_one("#label-2")
        zero_label = str(zero_button.label)
        assert "Label 2" in zero_label


@pytest.mark.asyncio
async def test_shortcut_focus_works():
    """Test `shortcut_focus_works` behavior."""
    controls = FilterControls()
    labels = _make_labels(6)
    fb = FilterBar(labels=labels, controls=controls)

    app = _FilterBarTestApp(fb)
    async with app.run_test(size=(120, 20)) as pilot:
        await pilot.pause()

        fb.focus_start_date()
        await pilot.pause()
        start_input = fb.query_one("#start-date")
        assert start_input.has_focus

        fb.focus_search()
        await pilot.pause()
        search_input = fb.query_one("#search-input")
        assert search_input.has_focus


@pytest.mark.asyncio
async def test_this_year_button_sets_dates():
    """Clicking 'Dieses Jahr' populates start/end date inputs with current year boundaries."""
    from datetime import date

    controls = FilterControls()
    fb = FilterBar(labels=_make_labels(2), controls=controls)
    app = _FilterBarTestApp(fb)

    async with app.run_test(size=(120, 20)) as pilot:
        await pilot.pause()
        btn = fb.query_one("#this-year-btn")
        await pilot.click(btn)
        await pilot.pause()

        year = date.today().year
        start_input = fb.query_one("#start-date")
        end_input = fb.query_one("#end-date")
        assert start_input.value == f"01.01.{year}"
        assert end_input.value == f"31.12.{year}"
        assert controls.start_date_text == f"01.01.{year}"
        assert controls.end_date_text == f"31.12.{year}"


@pytest.mark.asyncio
async def test_default_dates_shown_in_inputs():
    """FilterBar constructed with default_start/default_end shows those values."""
    controls = FilterControls()
    controls.start_date_text = "08.04.2026"
    controls.end_date_text = "07.07.2026"
    fb = FilterBar(labels=_make_labels(2), controls=controls)
    app = _FilterBarTestApp(fb)

    async with app.run_test(size=(120, 20)) as pilot:
        await pilot.pause()
        start_input = fb.query_one("#start-date")
        end_input = fb.query_one("#end-date")
        assert start_input.value == "08.04.2026"
        assert end_input.value == "07.07.2026"
