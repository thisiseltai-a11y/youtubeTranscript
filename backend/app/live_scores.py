"""
live_scores.py

Real live EPL scores from API-Football (api-football.com), separate from
the Dixon-Coles prediction model — this is actual results, not a forecast.

Requires API_FOOTBALL_KEY to be set (a free-tier key is enough for
light traffic: 100 requests/day). If it's not set, /live-scores just
returns an empty list rather than failing the whole app.

Caches responses in memory for CACHE_SECONDS so N visitors hitting our
/live-scores endpoint only cost us one upstream API-Football call per
cache window, not one per visitor — important given the free tier's
100 requests/day cap.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import date

import requests

logger = logging.getLogger("dixoncoles.live_scores")

API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
PREMIER_LEAGUE_ID = 39
CACHE_SECONDS = 30

_lock = threading.Lock()
_cache: dict = {"fetched_at": 0.0, "data": []}


def _current_season_year(today: date) -> int:
    """API-Football's `season` param is the year the season started (Aug)."""
    return today.year if today.month >= 8 else today.year - 1


def _api_key() -> str | None:
    return os.environ.get("API_FOOTBALL_KEY")


def _status_label(status_short: str, elapsed) -> str:
    if status_short == "NS":
        return "Not started"
    if status_short == "HT":
        return "Half-time"
    if status_short in ("FT", "AET", "PEN"):
        return "Full-time"
    if status_short in ("1H", "2H", "ET", "BT", "P", "LIVE") and elapsed is not None:
        return f"{elapsed}'"
    return status_short


def fetch_today_scores() -> list[dict]:
    """Today's EPL fixtures with live/current scores, cached briefly."""
    key = _api_key()
    if not key:
        logger.info("API_FOOTBALL_KEY not set; /live-scores will return an empty list")
        return []

    with _lock:
        age = time.time() - _cache["fetched_at"]
        if age < CACHE_SECONDS:
            return _cache["data"]

    today = date.today()
    try:
        resp = requests.get(
            f"{API_FOOTBALL_BASE}/fixtures",
            headers={"x-apisports-key": key},
            params={
                "league": PREMIER_LEAGUE_ID,
                "season": _current_season_year(today),
                "date": today.isoformat(),
            },
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.warning("API-Football request failed: %s", exc)
        with _lock:
            return _cache["data"]

    results = []
    for item in payload.get("response", []):
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        status = fixture.get("status", {})
        results.append({
            "fixture_id": fixture.get("id"),
            "kickoff": fixture.get("date"),
            "status_short": status.get("short"),
            "status_label": _status_label(status.get("short"), status.get("elapsed")),
            "home_team": teams.get("home", {}).get("name"),
            "away_team": teams.get("away", {}).get("name"),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
        })

    with _lock:
        _cache["fetched_at"] = time.time()
        _cache["data"] = results
    return results
