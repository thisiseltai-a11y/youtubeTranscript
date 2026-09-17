"""
main.py

FastAPI entrypoint. Fits the model once at startup, then refits daily via
a background scheduler (not on every request). Endpoints just read the
in-memory cache maintained by service.ModelService.
"""
import logging
from contextlib import asynccontextmanager
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .backtest_summary import load_backtest_summary
from .live_scores import fetch_today_scores
from .schemas import (
    BacktestSummary,
    BetEvaluationOut,
    EvaluateBetRequest,
    FixturePrediction,
    LiveScore,
    ModelStatus,
    TeamRating,
)
from .service import evaluate_match_odds, model_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dixoncoles.api")

scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Fitting model at startup...")
    model_service.refresh()
    scheduler.add_job(
        model_service.refresh,
        CronTrigger(hour=6, minute=0, timezone="UTC"),
        id="daily_refit",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="gambitParlay API",
    description="Wraps a backtested Dixon-Coles Poisson model for EPL match predictions.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status", response_model=ModelStatus)
def status():
    try:
        return {"status": "ready", "fitted_at": model_service.fitted_at().isoformat()}
    except RuntimeError:
        return {"status": "not_ready", "fitted_at": ""}


@app.get("/ratings", response_model=List[TeamRating])
def get_ratings():
    try:
        return model_service.ratings()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Model is still warming up, try again shortly")


@app.get("/fixtures", response_model=List[FixturePrediction])
def get_fixtures():
    try:
        return model_service.next_fixtures()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Model is still warming up, try again shortly")


@app.post("/evaluate-bet", response_model=List[BetEvaluationOut])
def evaluate_bet(req: EvaluateBetRequest):
    if not req.market_decimal_odds:
        raise HTTPException(status_code=400, detail="market_decimal_odds cannot be empty")
    missing = set(req.market_decimal_odds) - set(req.model_probs)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"model_probs is missing outcomes present in market_decimal_odds: {sorted(missing)}",
        )
    bets = evaluate_match_odds(
        req.model_probs,
        req.market_decimal_odds,
        kelly_frac=req.kelly_frac,
        min_edge=req.min_edge,
    )
    return [
        {
            "outcome": b.outcome,
            "model_prob": b.model_prob,
            "market_prob_devigged": b.market_prob_devigged,
            "decimal_odds": b.decimal_odds,
            "edge": b.edge,
            "kelly_stake_pct": b.kelly_stake_pct,
        }
        for b in bets
    ]


@app.get("/live-scores", response_model=List[LiveScore])
def live_scores():
    """Real EPL scores for today from API-Football — not model output.
    Returns an empty list (not an error) if API_FOOTBALL_KEY isn't configured."""
    return fetch_today_scores()


@app.get("/backtest-summary", response_model=BacktestSummary)
def backtest_summary():
    try:
        return load_backtest_summary()
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Backtest summary not generated yet — run scripts/generate_backtest_summary.py",
        )
