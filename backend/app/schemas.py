"""Pydantic request/response models for the API."""
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TeamRating(BaseModel):
    team: str
    attack: float
    defense: float
    net_rating: float
    current_season_matches: int
    thin_data: bool
    form_last5: List[str]
    goals_scored_per_game: Optional[float]
    goals_conceded_per_game: Optional[float]


class FixturePrediction(BaseModel):
    date: str
    home_team: str
    away_team: str
    home_win: float
    draw: float
    away_win: float
    expected_home_goals: float
    expected_away_goals: float
    over_2_5: float
    under_2_5: float
    btts_yes: float
    btts_no: float
    home_thin_data: bool
    away_thin_data: bool


class EvaluateBetRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_probs: Dict[str, float] = Field(
        ..., examples=[{"home_win": 0.55, "draw": 0.25, "away_win": 0.20}]
    )
    market_decimal_odds: Dict[str, float] = Field(
        ..., examples=[{"home_win": 1.95, "draw": 3.60, "away_win": 4.20}]
    )
    kelly_frac: float = 0.25
    min_edge: float = 0.02


class BetEvaluationOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    outcome: str
    model_prob: float
    market_prob_devigged: float
    decimal_odds: float
    edge: float
    kelly_stake_pct: float


class BacktestSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    generated_at: str
    date_range: str
    n_matches: int
    model_accuracy: float
    model_log_loss: float
    model_rps: float
    baseline_accuracy: float
    baseline_log_loss: float
    baseline_rps: float
    notes: str


class ModelStatus(BaseModel):
    status: str
    fitted_at: str


class LiveScore(BaseModel):
    fixture_id: Optional[int]
    kickoff: Optional[str]
    status_short: Optional[str]
    status_label: Optional[str]
    home_team: Optional[str]
    away_team: Optional[str]
    home_goals: Optional[int]
    away_goals: Optional[int]
