"""Webshare rotating-residential-proxy configuration, shared by the
captions path (youtube-transcript-api) and the yt-dlp paths (metadata
lookup + Whisper audio download).

Routing outbound YouTube requests through a rotating residential IP pool
is the standard fix for cloud-IP blocking at real traffic scale - a
single server IP (or a single cookie-authenticated account) can only
absorb so much volume before it gets flagged too. See README for details
and a link to set up a Webshare account.
"""
from __future__ import annotations

from typing import Optional

from youtube_transcript_api.proxies import WebshareProxyConfig

from . import config

_webshare_config: Optional[WebshareProxyConfig] = None
_resolved = False


def get_webshare_config() -> Optional[WebshareProxyConfig]:
    """The youtube-transcript-api proxy config object, or None if unconfigured."""
    global _webshare_config, _resolved
    if _resolved:
        return _webshare_config
    _resolved = True

    if not config.PROXY_ENABLED:
        return None

    locations = [
        loc.strip() for loc in config.WEBSHARE_PROXY_LOCATIONS.split(",") if loc.strip()
    ]
    _webshare_config = WebshareProxyConfig(
        proxy_username=config.WEBSHARE_PROXY_USERNAME,
        proxy_password=config.WEBSHARE_PROXY_PASSWORD,
        filter_ip_locations=locations or None,
    )
    return _webshare_config


def get_proxy_url() -> Optional[str]:
    """The same Webshare proxy, as a plain URL string for yt-dlp's `proxy` option."""
    webshare = get_webshare_config()
    return webshare.url if webshare else None
