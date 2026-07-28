"""Picker widget for selecting a format to download."""

from typing import Any

from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option
from yt_dlp.utils import format_bytes

_GUTTER = "  "
_HEADER_ID = "__header__"
MARKER_ARROW = "›"
MARKER_DOT = "·"

def _format_bitrate(fmt: dict[str, Any]) -> str:
    tbr = fmt.get("tbr")
    return f"{tbr:.0f}k" if tbr else "?"

def _format_size(fmt: dict[str, Any]) -> str:
    if size := fmt.get("filesize"):
        return format_bytes(size)
    if approx := fmt.get("filesize_approx"):
        return f"~{format_bytes(approx)}"
    return "?"

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

    class FormatChosen(Message):
        """Message that FormatPicker bubbles up to the app on selection - it's just the format_id."""
        def __init__(self, format_id: str) -> None:
            self.format_id = format_id
            super().__init__()

    def __init__(self, **kwargs) -> None:
        # compact=True removes the border around the input - we don't have to fight the native border CSS
        super().__init__(compact=True, **kwargs)
        self._labels: dict[str, str] = {}
        self.display = False  # Nothing to pick until set_formats() is called

    # Redraw the option list markers when hovering (i.e., register the mouse event)
    def on_mount(self) -> None:
        self.watch(self, "_mouse_hovering_over", self._redraw_markers, init=False)

    def set_formats(self, formats: list[dict[str, Any]]):
        # Calculate column widths to get table alignment.
        # One-liner looks messy, but it's basically making one big array of values and doing a max().
        # We can skip calculating size since it's always the last column.
        id_w = max([len("ID")] + [len(f.get("format_id", "")) for f in formats])
        ext_w = max([len("EXT")] + [len(f.get("ext", "")) for f in formats])
        quality_w = max([len("QUALITY")] + [len(f.get("resolution", "")) for f in formats])
        bitrate_w = max([len("BITRATE")] + [len(_format_bitrate(f)) for f in formats])

        # Helper function to quickly create an aligned row based on the values above.
        # < is: left-align & pad with spaces on the right
        def row(id: str, ext: str, quality: str, bitrate: str, size: str) -> str:
            return f"{id:<{id_w}} {ext:<{ext_w}}  {quality:<{quality_w}}  {bitrate:<{bitrate_w}}  {size}"

        self.clear_options()
        self._labels = {}

        # Add header "row" as a disabled option
        self.add_option(Option(f"{_GUTTER}{row("ID", "EXT", "QUALITY", "BITRATE", "SIZE")}", id=_HEADER_ID, disabled=True))
        for fmt in formats:
            format_id = fmt.get("format_id")
            label = row(format_id, fmt.get("ext", ""), fmt.get("resolution", ""), _format_bitrate(fmt), _format_size(fmt))
            self._labels[format_id] = label
            self.add_option(Option(label, id=format_id))
        if formats:
            self.highlighted = 1
        self.display = True

    def hide(self) -> None:
        """Empty the list and take it off screen - the picker owns its own visibility."""
        self.clear_options()
        self._labels = {}
        self.display = False

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        self._redraw_markers()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()  # Kills the built-in OptionSelected message and prevents that from bubbling up.
        self.post_message(self.FormatChosen(event.option_id))

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
