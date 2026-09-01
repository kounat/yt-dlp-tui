"""Wrapper for yt-dlp - doesn't know about the UI."""

import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from yt_dlp import YoutubeDL
from yt_dlp.utils import sanitize_filename

DOWNLOAD_DIR = Path.cwd();
SOCKET_TIMEOUT = 10

# frozen - class is immutable
# slots - catches typos and saves memory by using a fixed-size array for attributes
@dataclass(frozen=True, slots=True)
class VideoInfo:
    url: str
    title: str
    formats: list[dict[str, Any]]
    thumbnails: list[dict[str, Any]]

def _format_kind(fmt: dict[str, Any]) -> str:
    return "audio" if fmt.get("vcodec") in (None, "none") else "video"

def _is_media(fmt: dict[str, Any]) -> bool:
    return not (fmt.get("vcodec") == "none" and fmt.get("acodec") == "none")

def _quality_key(fmt: dict[str, Any]) -> tuple[int, float]:
    return (fmt.get("height") or 0, fmt.get("tbr") or 0)

def filter_formats(formats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group formats by extension, keeping the highest quality format in the list."""
    best: dict[str, dict[str, Any]] = {}
    for fmt in formats:
        if not _is_media(fmt):
            continue
        key = (fmt.get("ext"), _format_kind(fmt))
        # Python does a lexicographical comparison, so it checks the first element, then the second (if the first is equal), etc.
        if key not in best or _quality_key(fmt) > _quality_key(best[key]):
            best[key] = fmt
    return list(best.values())

def _thumbnail_ext(url: str) -> str:
    return Path(urlparse(url).path).suffix.lstrip(".") or "img"

def _thumbnail_score(thumb: dict[str, Any]) -> tuple[int, int]:
    return (thumb.get("preference") or 0, (thumb.get("width") or 0) * (thumb.get("height") or 0))

def best_thumbnails(thumbnails: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for thumb in thumbnails:
        if not thumb.get("url"):
            continue
        ext = _thumbnail_ext(thumb["url"])
        if ext not in best or _thumbnail_score(thumb) > _thumbnail_score(best[ext]):
            best[ext] = {**thumb, "ext": ext}
    return sorted(best.values(), key=lambda t: t["ext"])

def thumbnail_format(thumb: dict[str, Any]) -> dict[str, Any]:
    width, height = thumb.get("width"), thumb.get("height")
    return {
        "format_id": thumb["ext"],
        "ext": thumb["ext"],
        "resolution": f"{width}x{height}" if width and height else "image",
    }

def fetch_info(url: str) -> VideoInfo:
    with YoutubeDL({"socket_timeout": SOCKET_TIMEOUT}) as ydl:
        info = ydl.extract_info(url, download=False)
    return VideoInfo(
        url=url,
        title=info.get("title", url),
        formats=info.get("formats", []),
        thumbnails=best_thumbnails(info.get("thumbnails") or []),
    )

def download_url(url: str, format_id: str) -> None:
    with YoutubeDL({
        "format": format_id,
        # pathlib overrides __truediv__ to allow this funky string concatenation!
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        # Same title + ext across formats would otherwise be skipped as already downloaded
        "overwrites": True,
    }) as ydl:
        ydl.download([url])

def download_thumbnail(url: str, title: str) -> None:
    dest = DOWNLOAD_DIR / f"{sanitize_filename(title)}.{_thumbnail_ext(url)}"
    with urllib.request.urlopen(url, timeout=SOCKET_TIMEOUT) as response:
        dest.write_bytes(response.read())
