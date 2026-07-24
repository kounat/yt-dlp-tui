from textual.app import App, ComposeResult
from textual.widgets import Footer

class TUIApp(App):
    BINDINGS = [
        ("ctrl+c", "nothing")  # Suppress built-in Textual pop-up from Ctrl+C
    ]

    def compose(self) -> ComposeResult:
        yield Footer()
