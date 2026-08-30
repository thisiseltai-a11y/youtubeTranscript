"""yt-dlp options shared by both the metadata lookup and the audio
download path (cookie support for resilience against cloud-IP blocking).
"""
from __future__ import annotations

import base64
from pathlib import Path

from . import config

_cookiefile_path: Path | None = None
_resolved = False


def _get_cookiefile() -> Path | None:
    global _cookiefile_path, _resolved
    if _resolved:
        return _cookiefile_path
    _resolved = True

    if not config.YTDLP_COOKIES_B64:
        return None

    try:
        raw = base64.b64decode(config.YTDLP_COOKIES_B64)
    except (ValueError, TypeError):
        return None

    path = config.TMP_DIR / "yt_cookies.txt"
    path.write_bytes(raw)
    _cookiefile_path = path
    return path


def common_ydl_opts() -> dict:
    """Extra yt-dlp options to merge into every request (currently just
    cookies, when configured).
    """
    cookiefile = _get_cookiefile()
    if cookiefile:
        return {"cookiefile": str(cookiefile)}
    return {}
