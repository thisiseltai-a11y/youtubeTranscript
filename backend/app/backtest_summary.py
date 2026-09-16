"""Reads the stored backtest summary (see scripts/generate_backtest_summary.py)."""
import json
from pathlib import Path

SUMMARY_PATH = Path(__file__).resolve().parent / "data" / "backtest_summary.json"


def load_backtest_summary() -> dict:
    with open(SUMMARY_PATH) as f:
        return json.load(f)
