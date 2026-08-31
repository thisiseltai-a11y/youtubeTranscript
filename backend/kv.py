"""Thin client for the Upstash Redis REST API (single-command endpoint).

Shared by anything that needs durable, cross-invocation storage on Vercel
(the transcript cache, The Lot's saved state, ...) - see config.KV_ENABLED
for how it's configured via the "Upstash for Redis" Marketplace integration.
"""
from __future__ import annotations

import requests

from . import config


def command(cmd: list) -> object:
    resp = requests.post(
        config.KV_REST_API_URL,
        headers={"Authorization": f"Bearer {config.KV_REST_API_TOKEN}"},
        json=cmd,
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json().get("result")
