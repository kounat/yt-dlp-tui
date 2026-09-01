import threading
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal
from textual.theme import Theme
from textual.timer import Timer
from textual.widgets import Input, Static
from yt_dlp.utils import YoutubeDLError, remove_terminal_sequences

from yt_dlp_tui.engine import (
    DOWNLOAD_DIR,
    VideoInfo,
    download_thumbnail,
    download_url,
    fetch_info,
    filter_formats,
    thumbnail_format,
)
from yt_dlp_tui.picker import FormatPicker

INPUT_ARROW = "❯"
FETCH_TIMEOUT = 10.0

DEFAULT_THEME = Theme(
    name = "default",
    primary="#AC5EFF",
    error="ansi_red",
    success="ansi_green",
    dark=True,
)

def _display_path(path: Path) -> str:
    home = Path.home()
    if path == home:
        return "~"
    if path.is_relative_to(home):
        return f"~/{path.relative_to(home)}"
    return str(path)

def _run_daemon(target, *args) -> None:
    """Run blocking work on a thread the interpreter won't wait for on the way out.

    Textual's @work(thread=True) hands the job to asyncio's default executor, whose
    threads get joined at shutdown - so quitting after a timeout would block for up to
    five minutes on a yt-dlp call we stopped caring about. A daemon thread is
    killed at exit instead: nothing here outlives the UI.
    """
    def run() -> None:
        try:
            target(*args)
        except RuntimeError:
            # call_from_thread raises once the app is gone
            pass

    threading.Thread(target=run, daemon=True).start()

class TUIApp(App):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("ctrl+c", "nothing")  # Suppress built-in Textual pop-up from Ctrl+C
    ]
    CSS_PATH = "app.tcss"

    def __init__(self) -> None:
        super().__init__(ansi_color=True)
        self._video_info: VideoInfo | None = None
        self._fetch_timeout: Timer | None = None
        self._fetch_token = 0

    def compose(self) -> ComposeResult:
        yield Static(f"Saving to: {_display_path(DOWNLOAD_DIR)}", id="dest")
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

        status = self.query_one("#status", Static)
        status.update("Loading...")
        status.set_classes("active")

        self._fetch_token += 1
        _run_daemon(self.fetch_formats, event.value.strip(), self._fetch_token)
        self._fetch_timeout = self.set_timer(FETCH_TIMEOUT, self.show_timeout)

    # Runs off the renderer thread so a slow yt-dlp call can't freeze the UI.
    def fetch_formats(self, url: str, token: int) -> None:
        try:
            info = fetch_info(url)
        except YoutubeDLError as error:
            # call_from_thread - safely reach out to main renderer thread to update UI.
            self.call_from_thread(self.fetch_finished, token, None, str(error))
            return
        self.call_from_thread(self.fetch_finished, token, info, None)

    def fetch_finished(self, token: int, info: VideoInfo | None, error: str | None) -> None:
        # Staleness check to ignore calls that might have returned late.
        if token != self._fetch_token:
            return
        if error is not None:
            self.show_error(error)
        else:
            self.show_formats(info)

    def show_timeout(self) -> None:
        # A thread can't be killed mid-flight, so we stop listening to it by increasing the token.
        self._fetch_token += 1
        self.show_error(f"Timed out after {FETCH_TIMEOUT:.0f}s - is the URL correct?")

    def show_error(self, message: str) -> None:
        self._cancel_fetch_timeout()
        status = self.query_one("#status", Static)
        status.update(remove_terminal_sequences(message))
        status.set_classes("error")
        self.reset(clear=False)  # Keep the URL around so it can be fixed, not retyped

    def show_formats(self, info: VideoInfo) -> None:
        self._cancel_fetch_timeout()
        self._video_info = info

        status = self.query_one("#status", Static)
        status.update(f"{info.title} - Select a format")
        status.set_classes("active")

        formats = filter_formats(info.formats)
        formats += [thumbnail_format(thumb) for thumb in info.thumbnails]

        picker = self.query_one(FormatPicker)
        picker.set_formats(formats)
        picker.focus()

    # Automatically hooked up to the FormatPicker message using this syntax (metaprogramming magic!):
    # on_<containing_class_name>_<message_class_name>
    def on_format_picker_format_chosen(self, event: FormatPicker.FormatChosen) -> None:
        self.query_one(FormatPicker).hide()
        status = self.query_one("#status", Static)
        thumb = self._thumbnail_for(event.format_id)
        if thumb is not None:
            status.update(f"Downloading {thumb['ext']} thumbnail for {self._video_info.title}...")
        else:
            status.update(f"Downloading {self._video_info.title} in format {event.format_id}...")
        _run_daemon(self.run_download, self._video_info, event.format_id)

    def _thumbnail_for(self, format_id: str) -> dict | None:
        return next((t for t in self._video_info.thumbnails if t["ext"] == format_id), None)

    def run_download(self, info: VideoInfo, format_id: str) -> None:
        thumb = next((t for t in info.thumbnails if t["ext"] == format_id), None)
        try:
            if thumb is not None:
                download_thumbnail(thumb["url"], info.title)
            else:
                download_url(info.url, format_id)
        except (YoutubeDLError, OSError) as error:
            self.call_from_thread(self.show_error, str(error))
            return
        self.call_from_thread(self.show_download_complete, info.title)

    def show_download_complete(self, title: str) -> None:
        status = self.query_one("#status", Static)
        status.update(f"Successfully downloaded {title}!")
        status.set_classes("success")
        self.reset()

    def reset(self, *, clear: bool = True) -> None:
        self.query_one(FormatPicker).hide()

        input = self.query_one(URLInput)
        if clear:
            input.value = ""
        input.disabled = False
        input.focus()

        self._video_info = None

    def _cancel_fetch_timeout(self) -> None:
        if self._fetch_timeout is not None:
            self._fetch_timeout.stop()
            self._fetch_timeout = None

class URLInput(Input):
    """Tiny replacement to the Input widget to allow Ctrl+C to wipe the text out when focused."""
    def action_copy(self) -> None:
        if self.selected_text:
            self.app.copy_to_clipboard(self.selected_text)
        else:
            self.value = ""
