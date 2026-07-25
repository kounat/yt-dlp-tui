"""Picker widget for selecting a format to download."""

from typing import Any

from textual.widgets import OptionList
from textual.widgets.option_list import Option


class FormatPicker(OptionList):
    def set_formats(self, formats: list[dict[str, Any]]):
        self.clear_options()
        for fmt in formats:
            label = fmt.get("format_id")
            self.add_option(Option(label, id=fmt.get("format_id")))
