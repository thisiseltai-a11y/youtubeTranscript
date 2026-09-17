"""
service.py

Loads and refits the Dixon-Coles model from ../model (the user's original,
unmodified model code) on a schedule, and caches the results in memory so
API requests are served instantly instead of refitting per-request.

This file only wraps model/*.py — it does not reimplement any modeling
logic (fitting, probabilities, staking math all live in model/).
"""
from __future__ import annotations

import json
import logging
import sys
import threading
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "model"
sys.path.insert(0, str(MODEL_DIR))

from data_loader import load_all_seasons  # noqa: E402
from poisson_model import DixonColesModel  # noqa: E402
from staking import evaluate_match_odds  # noqa: E402
import main as model_cli  # noqa: E402  (reuse load_upcoming_fixtures as-is)

logger = logging.getLogger("dixoncoles.service")

THIN_DATA_MIN_MATCHES = 6
DATA_DIR = MODEL_DIR / "data"
FOOTBALL_JSON_BASE = "https://raw.githubusercontent.com/openfootball/football.json/master"


def current_season_str(today: date) -> str:
    """e.g. 2026-09-16 -> '2026-27' (EPL seasons run August-May)."""
    year = today.year
    start, end = (year, year + 1) if today.month >= 8 else (year - 1, year)
    return f"{start}-{str(end)[2:]}"


def current_season_start(today: date) -> date:
    year = today.year
    start_year = year if today.month >= 8 else year - 1
    return date(start_year, 8, 1)


def refresh_current_season_file(today: Optional[date] = None) -> None:
    """Re-pulls only the current season's file (finished seasons don't change)."""
    today = today or date.today()
    season = current_season_str(today)
    url = f"{FOOTBALL_JSON_BASE}/{season}/en.1.json"
    dest = DATA_DIR / f"en1_{season}.json"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        dest.write_text(json.dumps(data))
        logger.info("Refreshed %s season data from %s", season, url)
    except Exception as exc:  # network hiccup, season file not published yet, etc.
        logger.warning("Could not refresh %s season data (%s); using cached copy.", season, exc)


@dataclass
class RatingsCache:
    fitted_at: datetime
    model: DixonColesModel
    matches: pd.DataFrame
    current_season_counts: dict


class ModelService:
    """Holds the current fitted model + derived data behind a lock, refreshed on a schedule."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: Optional[RatingsCache] = None

    def refresh(self) -> None:
        refresh_current_season_file()
        matches = load_all_seasons(data_dir=str(DATA_DIR))
        model = DixonColesModel(xi=0.0018).fit(matches)

        season_start = pd.Timestamp(current_season_start(date.today()))
        current = matches[matches["date"] >= season_start]
        counts = {
            t: int(((current.home_team == t) | (current.away_team == t)).sum())
            for t in model.teams_
        }

        cache = RatingsCache(
            fitted_at=datetime.now(timezone.utc),
            model=model,
            matches=matches,
            current_season_counts=counts,
        )
        with self._lock:
            self._cache = cache
        logger.info("Model refit complete: %d teams, %d matches", len(model.teams_), len(matches))

    def _get_cache(self) -> RatingsCache:
        with self._lock:
            if self._cache is None:
                raise RuntimeError("Model not yet fitted")
            return self._cache

    def is_thin(self, cache: RatingsCache, team: str) -> bool:
        return cache.current_season_counts.get(team, 0) < THIN_DATA_MIN_MATCHES

    def fitted_at(self) -> datetime:
        return self._get_cache().fitted_at

    def team_form(self, cache: RatingsCache, team: str) -> dict:
        """Last-5 results (most recent first) and career scored/conceded-per-game,
        computed directly from loaded match history — not model output."""
        m = cache.matches
        team_matches = m[(m.home_team == team) | (m.away_team == team)].sort_values("date")
        if len(team_matches) == 0:
            return {"form_last5": [], "goals_scored_per_game": None, "goals_conceded_per_game": None}

        scored, conceded, form = [], [], []
        for _, row in team_matches.iterrows():
            is_home = row["home_team"] == team
            gf = row["home_goals"] if is_home else row["away_goals"]
            ga = row["away_goals"] if is_home else row["home_goals"]
            scored.append(gf)
            conceded.append(ga)
            form.append("W" if gf > ga else "L" if gf < ga else "D")

        return {
            "form_last5": form[-5:][::-1],
            "goals_scored_per_game": round(sum(scored) / len(scored), 2),
            "goals_conceded_per_game": round(sum(conceded) / len(conceded), 2),
        }

    def ratings(self) -> list[dict]:
        cache = self._get_cache()
        rows = []
        for _, r in cache.model.ratings_table().iterrows():
            team = r["team"]
            form = self.team_form(cache, team)
            rows.append({
                "team": team,
                "attack": float(r["attack"]),
                "defense": float(r["defense"]),
                "net_rating": float(r["net_rating"]),
                "current_season_matches": cache.current_season_counts.get(team, 0),
                "thin_data": self.is_thin(cache, team),
                "form_last5": form["form_last5"],
                "goals_scored_per_game": form["goals_scored_per_game"],
                "goals_conceded_per_game": form["goals_conceded_per_game"],
            })
        return rows

    def next_fixtures(self) -> list[dict]:
        cache = self._get_cache()
        upcoming = model_cli.load_upcoming_fixtures(data_dir=str(DATA_DIR))
        if not len(upcoming):
            return []
        next_date = upcoming["date"].min()
        todays = upcoming[upcoming["date"] == next_date]

        out = []
        for _, row in todays.iterrows():
            h, a = row["home_team"], row["away_team"]
            if h not in cache.model.attack_ or a not in cache.model.attack_:
                continue  # team with no fitted rating yet (e.g. brand-new promotion, zero matches)
            p = cache.model.match_probabilities(h, a)
            out.append({
                "date": row["date"].date().isoformat(),
                "home_team": h,
                "away_team": a,
                "home_win": p["home_win"],
                "draw": p["draw"],
                "away_win": p["away_win"],
                "expected_home_goals": p["expected_home_goals"],
                "expected_away_goals": p["expected_away_goals"],
                "over_2_5": p["over_2_5"],
                "under_2_5": p["under_2_5"],
                "btts_yes": p["btts_yes"],
                "btts_no": p["btts_no"],
                "home_thin_data": self.is_thin(cache, h),
                "away_thin_data": self.is_thin(cache, a),
            })
        return out


model_service = ModelService()
