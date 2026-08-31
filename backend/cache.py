"""Transcript cache, keyed by video ID.

Two backends:
- Upstash Redis (via the "Upstash for Redis" Vercel Marketplace
  integration, which sets KV_REST_API_URL / KV_REST_API_TOKEN) - durable,
  shared across serverless invocations. Used automatically when configured.
- A local JSON file per video under CACHE_DIR - used for local dev, or as
  a best-effort (non-durable) fallback if the KV env vars aren't set on
  Vercel.

Either way, a cache failure never breaks the main request - we log and
treat it as a miss/no-op rather than raising.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import requests

from . import config, kv

logger = logging.getLogger(__name__)

_KEY_PREFIX = "transcript:"


def _path(video_id: str):
    return config.CACHE_DIR / f"{video_id}.json"


def get(video_id: str) -> Optional[dict]:
    if config.KV_ENABLED:
        try:
            raw = kv.command(["GET", _KEY_PREFIX + video_id])
        except (requests.RequestException, ValueError) as exc:
            logger.warning("KV cache read failed, treating as a miss: %s", exc)
            return None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    path = _path(video_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def set(video_id: str, data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False)

    if config.KV_ENABLED:
        try:
            kv.command(["SET", _KEY_PREFIX + video_id, payload])
        except requests.RequestException as exc:
            logger.warning("KV cache write failed (continuing without caching): %s", exc)
        return

    try:
        _path(video_id).write_text(payload)
    except OSError as exc:
        logger.warning("Local cache write failed (continuing without caching): %s", exc)
