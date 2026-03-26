"""Help screen — modal overlay listing all key bindings."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class HelpScreen(ModalScreen[None]):
    """Modal overlay showing all available key bindings."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    #help-container {
        width: 60;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: tall $primary;
    }
    #help-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #help-body {
        margin-bottom: 1;
    }
    #help-close {
        align: center middle;
        width: 100%;
    }
    """

    BINDINGS = [("escape", "close", "Close"), ("f1", "close", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Static("[b]GroupAlarm TUI — Key Bindings[/b]", id="help-title")
            yield Static(
                "[b]Navigation[/b]\n"
                "  ↑/↓         Navigate appointment list\n"
                "  Enter       Select appointment\n"
                "  ←/→         Switch between list and detail\n"
                "  Ctrl+F      Search appointments\n"
                "  Ctrl+T      Focus date filter\n"
                "\n"
                "[b]Actions[/b]\n"
                "  e           Enter edit mode\n"
                "  Ctrl+S      Save changes (with confirmation)\n"
                "  n           Create new appointment\n"
                "  d           Delete selected appointment\n"
                "  x           Export filtered list to Excel\n"
                "  i           Add GA-IMPORTER tokens to filtered\n"
                "  r           Refresh appointment list\n"
                "\n"
                "[b]General[/b]\n"
                "  Escape      Cancel edit / close dialog\n"
                "  F1          This help screen\n"
                "  q           Quit (with unsaved changes check)\n"
                "\n"
                "[b]Terminal[/b]\n"
                "  Ctrl +/−    Zoom in/out\n",
                id="help-body",
            )
            yield Button("Close", id="help-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
