from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal
from textual.theme import Theme
from textual.widgets import Input, Static
from yt_dlp.utils import YoutubeDLError, remove_terminal_sequences

from yt_dlp_tui.engine import VideoInfo, fetch_info
from yt_dlp_tui.picker import FormatPicker

INPUT_ARROW = "❯"

DEFAULT_THEME = Theme(
    name = "default",
    primary="#8A7CDC",
    error="ansi_red",
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
            yield URLInput(placeholder="Paste a YouTube URL and hit Enter! (Ctrl+C to clear, Ctrl+Q to quit.)")
        yield Static("", id="status")
        yield FormatPicker()

    def on_mount(self) -> None:
        self.register_theme(DEFAULT_THEME)
        self.theme = "default"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.input.disabled = True
        self.fetch_formats(event.value.strip())

    # work - tells Textual to run this function on a separate thread than the renderer.
    # Not sure it matters in this case since nothing else is happening, but it's good practice.
    @work(thread=True)
    def fetch_formats(self, url: str):
        try:
            info = fetch_info(url)
        except YoutubeDLError as error:
            self.call_from_thread(self.show_error, str(error))
            return
        # call_from_thread - safely reach out to main renderer thread to update UI.
        self.call_from_thread(self.show_formats, info)

    def show_error(self, message: str) -> None:
        status = self.query_one("#status", Static)
        status.update(remove_terminal_sequences(message))
        status.set_classes("error")
        self.query_one(URLInput).disabled = False

    def show_formats(self, info: VideoInfo):
        status = self.query_one("#status", Static)
        status.update(f"{info.title} - Select a format")
        status.set_classes("active")

        picker = self.query_one(FormatPicker)
        picker.set_formats(info.formats)
        picker.focus()

    # Automatically hooked up to the FormatPicker message using this syntax (metaprogramming magic!):
    # on_<containing_class_name>_<message_class_name>
    def on_format_picker_format_chosen(self, event: FormatPicker.FormatChosen) -> None:
        self.query_one(FormatPicker).display = False
        status = self.query_one("#status", Static)
        status.update(f"Downloading {event.format_id}...")

class URLInput(Input):
    """Tiny replacement to the Input widget to allow Ctrl+C to wipe the text out when focused."""
    def action_copy(self) -> None:
        if self.selected_text:
            self.app.copy_to_clipboard(self.selected_text)
        else:
            self.value = ""
