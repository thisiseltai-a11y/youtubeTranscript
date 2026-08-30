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
    """Extra yt-dlp options to merge into every request.

    - `player_client`: YouTube's main "web" client is what triggers the
      "Sign in to confirm you're not a bot" wall on cloud/datacenter IPs
      (this is what most people hit running yt-dlp on any cloud provider,
      Vercel included). Falling back to the mobile clients' API surface
      sidesteps that check for most public videos, no cookies required.
      `web` stays last as a normal fallback for anything the others miss.
    - `cookiefile`: only added when YTDLP_COOKIES_B64 is configured - a
      stronger fix if the client-fallback trick above isn't enough on its
      own (see README).
    """
    opts: dict = {
        "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
    }
    cookiefile = _get_cookiefile()
    if cookiefile:
        opts["cookiefile"] = str(cookiefile)
    return opts
