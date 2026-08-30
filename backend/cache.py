"""Simple file-based cache, keyed by video ID.

A JSON file per video is plenty for a local prototype and needs no extra
infra. Swap for Redis/SQLite later if this needs to run multi-instance.
"""
from __future__ import annotations

import json
from typing import Optional

from . import config


def _path(video_id: str):
    return config.CACHE_DIR / f"{video_id}.json"


def get(video_id: str) -> Optional[dict]:
    path = _path(video_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def set(video_id: str, data: dict) -> None:
    path = _path(video_id)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
