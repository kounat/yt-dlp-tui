from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.widgets import Footer


class TUIApp(App):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("ctrl+c", "nothing")  # Suppress built-in Textual pop-up from Ctrl+C
    ]

    def compose(self) -> ComposeResult:
        yield Footer()
