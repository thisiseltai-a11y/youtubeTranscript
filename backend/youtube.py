"""URL parsing and video metadata lookup."""
from __future__ import annotations

import re
from typing import TypedDict
from urllib.parse import parse_qs, urlparse

import yt_dlp

from . import ytdlp_common
from .exceptions import InvalidURLError, VideoUnavailableError, YouTubeBlockedError

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

        # YouTube's bot-check response is easy to mistake for "video is
        # actually unavailable" - it isn't. It shows up on cloud/datacenter
        # IPs (including Vercel's) for otherwise-normal, public videos, so
        # it needs its own error rather than being told to the user as
        # "this video is private/deleted".
        if any(
            phrase in lowered
            for phrase in ("sign in to confirm", "not a bot", "confirm you're not a bot")
        ):
            raise YouTubeBlockedError(
                "YouTube is blocking automated requests from this server right "
                "now - this is a cloud-IP rate limit, not a problem with the "
                "video itself. See the README's YTDLP_COOKIES_B64 workaround."
            ) from exc

        # Phrases yt-dlp uses when it has confidently identified a
        # specific reason (private/deleted/terminated/age-gated) - NOT
        # YouTube's generic "Video unavailable" wall, which can also
        # appear behind an unrecognized bot-check or consent interstitial
        # and would otherwise cause a false positive here.
        if any(
            phrase in lowered
            for phrase in (
                "private video",
                "has been removed",
                "account associated with this video has been terminated",
                "this video is not available",
                "age-restricted",
                "age restricted",
            )
        ):
            raise VideoUnavailableError(
                "This video is private, deleted, age-restricted, or otherwise "
                f"unavailable. (Details: {message})"
            ) from exc

        # Anything else - including the generic "Video unavailable" message -
        # could genuinely be the video, or could be an unrecognized
        # bot-check/consent wall. Surface the real reason instead of
        # guessing which one it is.
        raise VideoUnavailableError(
            "Could not access this video. This may mean the video is "
            "genuinely unavailable, or that YouTube is blocking requests "
            f"from this server. (Details: {message})"
        ) from exc

    if info is None:
        raise VideoUnavailableError("Could not access this video.")

    return VideoMetadata(
        video_id=video_id,
        title=info.get("title") or video_id,
        duration=float(info.get("duration") or 0),
        webpage_url=info.get("webpage_url") or url,
    )
