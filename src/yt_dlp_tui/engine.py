"""Wrapper for yt-dlp - doesn't know about the UI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

DOWNLOAD_DIR = Path.cwd();

# frozen - class is immutable
# slots - catches typos and saves memory by using a fixed-size array for attributes
@dataclass(frozen=True, slots=True)
class VideoInfo:
    url: str
    title: str
    formats: list[dict[str, Any]]

def _format_kind(fmt: dict[str, Any]) -> str:
    return "audio" if fmt.get("vcodec") in (None, "none") else "video"

def _quality_key(fmt: dict[str, Any]) -> tuple[int, float]:
    return (fmt.get("height") or 0, fmt.get("tbr") or 0)

def filter_formats(formats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group formats by extension, keeping the highest quality format in the list."""
    best: dict[str, dict[str, Any]] = {}
    for fmt in formats:
        key = (fmt.get("ext"), _format_kind(fmt))
        # Python does a lexicographical comparison, so it checks the first element, then the second (if the first is equal), etc.
        if key not in best or _quality_key(fmt) > _quality_key(best[key]):
            best[key] = fmt
    return list(best.values())

def fetch_info(url: str) -> VideoInfo:
    with YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
    return VideoInfo(
        url=url,
        title=info.get("title", url),
        formats=info.get("formats", [])
    )

def download_url(url: str, format_id: str) -> None:
    with YoutubeDL({
        "format": format_id,
        # pathlib overrides __truediv__ to allow this funky string concatenation!
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
    }) as ydl:
        ydl.download([url])
