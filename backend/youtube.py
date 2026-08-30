"""URL parsing and video metadata lookup."""
from __future__ import annotations

import re
from typing import TypedDict
from urllib.parse import parse_qs, urlparse

import yt_dlp

from . import ytdlp_common
from .exceptions import InvalidURLError, VideoUnavailableError

_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

_ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


def extract_video_id(url: str) -> str:
    """Pull an 11-char YouTube video ID out of any common URL shape.

    Supports watch?v=, youtu.be/, /shorts/, /embed/, /live/, and a bare ID.
    """
    url = (url or "").strip()
    if not url:
        raise InvalidURLError("Please paste a YouTube URL.")

    # Allow pasting a bare video ID directly.
    if _VIDEO_ID_RE.match(url):
        return url

    if "://" not in url:
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise InvalidURLError(f"Could not parse URL: {exc}") from exc

    host = (parsed.hostname or "").lower()
    if host not in _ALLOWED_HOSTS:
        raise InvalidURLError("That doesn't look like a YouTube URL.")

    video_id = None
    if host in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.lstrip("/").split("/")[0]
    else:
        qs = parse_qs(parsed.query)
        if "v" in qs:
            video_id = qs["v"][0]
        else:
            for prefix in ("/shorts/", "/embed/", "/live/"):
                if parsed.path.startswith(prefix):
                    video_id = parsed.path[len(prefix):].split("/")[0]
                    break

    if not video_id or not _VIDEO_ID_RE.match(video_id):
        raise InvalidURLError("Couldn't find a video ID in that URL.")

    return video_id


class VideoMetadata(TypedDict):
    video_id: str
    title: str
    duration: float
    webpage_url: str


def get_video_metadata(video_id: str) -> VideoMetadata:
    """Look up title/duration/availability without downloading anything."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        **ytdlp_common.common_ydl_opts(),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        message = str(exc)
        lowered = message.lower()
        if any(
            phrase in lowered
            for phrase in (
                "private video",
                "video unavailable",
                "has been removed",
                "account associated with this video has been terminated",
                "this video is not available",
                "sign in to confirm",
                "age",
            )
        ):
            raise VideoUnavailableError(
                "This video is private, deleted, age-restricted, or otherwise unavailable."
            ) from exc
        raise VideoUnavailableError(f"Could not access this video: {message}") from exc

    if info is None:
        raise VideoUnavailableError("Could not access this video.")

    return VideoMetadata(
        video_id=video_id,
        title=info.get("title") or video_id,
        duration=float(info.get("duration") or 0),
        webpage_url=info.get("webpage_url") or url,
    )
