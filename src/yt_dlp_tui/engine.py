"""Wrapper for yt-dlp - doesn't know about the UI."""

from dataclasses import dataclass
from typing import Any

from yt_dlp import YoutubeDL


# frozen - class is immutable
# slots - catches typos and saves memory by using a fixed-size array for attributes
@dataclass(frozen=True, slots=True)
class VideoInfo:
    url: str
    title: str
    formats: list[dict[str, Any]]

def fetch_info(url: str) -> VideoInfo:
    with YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
    return VideoInfo(
        url=url,
        title=info.get("title", url),
        formats=info.get("formats", [])
    )
