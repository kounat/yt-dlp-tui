from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal
from textual.theme import Theme
from textual.widgets import Input, Static

from yt_dlp_tui.engine import list_formats

INPUT_ARROW = "❯"

DEFAULT_THEME = Theme(
    name = "default",
    primary="#8A7CDC",
    dark=True,
)

class TUIApp(App):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("ctrl+c", "nothing")  # Suppress built-in Textual pop-up from Ctrl+C
    ]
    CSS_PATH = "app.tcss"

    def __init__(self) -> None:
        super().__init__(ansi_color=True)

    def compose(self) -> ComposeResult:
        with Horizontal(id="input-box"):
            yield Static(INPUT_ARROW)
            yield Input(placeholder="Paste a YouTube URL and hit Enter! (Ctrl+Q to quit.)")

    def on_mount(self) -> None:
        self.register_theme(DEFAULT_THEME)
        self.theme = "default"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        url = event.value.strip()
        formats = list_formats(url)
        self.notify(f"Got Title: {formats.title}")
