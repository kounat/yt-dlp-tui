"""Picker widget for selecting a format to download."""

from typing import Any

from textual.widgets import OptionList
from textual.widgets.option_list import Option


class FormatPicker(OptionList):
    DEFAULT_CSS = """
        FormatPicker {
            background: ansi_default;

            &:focus > .option-list--option-highlighted {
                background: transparent;
                color: $accent;
                text-style: bold;
            }

            & > .option-list--option-hover {
                background: transparent;
                color: $text-muted;
            }
        }
    """

    def __init__(self, **kwargs) -> None:
        # compact=True removes the border around the input - we don't have to fight the native border CSS
        super().__init__(compact=True, **kwargs)

    def set_formats(self, formats: list[dict[str, Any]]):
        self.clear_options()
        for fmt in formats:
            label = fmt.get("format_id")
            self.add_option(Option(label, id=fmt.get("format_id")))
