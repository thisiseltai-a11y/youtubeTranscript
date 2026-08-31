"""Storage for The Lot's car list - a single shared JSON blob (there's only
ever one lot), not per-key like the transcript cache. Same two backends as
cache.py: Upstash Redis when configured, a local JSON file otherwise.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import requests

from . import config, kv
from .exceptions import LotSaveError

logger = logging.getLogger(__name__)

_KEY = "the-lot:state"


def _path():
    return config.CACHE_DIR / "the-lot.json"


def get() -> Optional[dict]:
    if config.KV_ENABLED:
        try:
            raw = kv.command(["GET", _KEY])
        except (requests.RequestException, ValueError) as exc:
            logger.warning("KV read failed for The Lot, treating as empty: %s", exc)
            return None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    path = _path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def set(data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False)

    if config.KV_ENABLED:
        try:
            kv.command(["SET", _KEY, payload])
        except requests.RequestException as exc:
            logger.warning("KV write failed for The Lot (change not saved): %s", exc)
            raise LotSaveError("Couldn't save The Lot's data right now.") from exc
        return

    try:
        _path().write_text(payload)
    except OSError as exc:
        logger.warning("Local write failed for The Lot (change not saved): %s", exc)
        raise LotSaveError("Couldn't save The Lot's data right now.") from exc
