"""Picker widget for selecting a format to download."""

from typing import Any

from textual.widgets import OptionList
from textual.widgets.option_list import Option

_GUTTER = "  "
_HEADER_ID = "__header__"
MARKER_ARROW = "›"
MARKER_DOT = "·"

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

            & > .option-list--option-disabled {
                color: $text-muted;
                text-style: bold;
            }
        }
    """

    def __init__(self, **kwargs) -> None:
        # compact=True removes the border around the input - we don't have to fight the native border CSS
        super().__init__(compact=True, **kwargs)
        self._labels: dict[str, str] = {}

    # Redraw the option list markers when hovering (i.e., register the mouse event)
    def on_mount(self) -> None:
        self.watch(self, "_mouse_hovering_over", self._redraw_markers, init=False)

    def set_formats(self, formats: list[dict[str, Any]]):
        self.clear_options()
        self.add_option(Option(f"{_GUTTER}ID", id=_HEADER_ID, disabled=True))

        self._labels = {}
        for fmt in formats:
            format_id = fmt.get("format_id")
            self._labels[format_id] = format_id
            self.add_option(Option(format_id, id=format_id))
        if formats:
            self.highlighted = 1

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        self._redraw_markers()

    def _redraw_markers(self) -> None:
        hovered = self._mouse_hovering_over
        for index, option in enumerate(self.options):
            if option.disabled:
                continue
            label = self._labels[option.id]
            if index == self.highlighted:
                marker = f"{MARKER_ARROW} "
            elif index == hovered:
                marker = f"{MARKER_DOT} "
            else:
                marker = "  "
            self.replace_option_prompt_at_index(index, f"{marker}{label}")
