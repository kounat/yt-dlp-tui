from typing import Any, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal
from textual.theme import Theme
from textual.widgets import Input, Static

from yt_dlp_tui.engine import fetch_info
from yt_dlp_tui.picker import FormatPicker

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
        yield FormatPicker()

    def on_mount(self) -> None:
        self.register_theme(DEFAULT_THEME)
        self.theme = "default"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.fetch_formats(event.value.strip())

    # work - tells Textual to run this function on a separate thread than the renderer.
    # Not sure it matters in this case since nothing else is happening, but it's good practice.
    @work(thread=True)
    def fetch_formats(self, url: str):
        info = fetch_info(url)
        # call_from_thread - safely reach out to main renderer thread to update UI.
        self.call_from_thread(self.show_formats, info.formats)

    def show_formats(self, formats: list[dict[str, Any]]):
        self.query_one(FormatPicker).set_formats(formats)
