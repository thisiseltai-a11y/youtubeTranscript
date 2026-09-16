"""
Regenerates backend/app/data/backtest_summary.json from a fresh walk-forward
backtest run against model/data. Not run per-request — re-run this manually
(or from a periodic job) whenever you want the trust/credibility numbers
refreshed against newer data.

Run: python3 backend/scripts/generate_backtest_summary.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "model"
sys.path.insert(0, str(MODEL_DIR))

from backtest import baseline_comparison, walk_forward_backtest  # noqa: E402
from data_loader import load_all_seasons  # noqa: E402

OUT_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "backtest_summary.json"


def main():
    matches = load_all_seasons(data_dir=str(MODEL_DIR / "data"))
    print(f"Loaded {len(matches)} matches ({matches.date.min().date()} to {matches.date.max().date()})")
    print("Running walk-forward backtest...")

    bt = walk_forward_backtest(matches, min_train_matches=380, xi=0.0018, refit_every_matches=20)
    baseline = baseline_comparison(bt, matches)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date_range": f"{matches.date.min().date()} to {matches.date.max().date()}",
        "n_matches": int(len(bt)),
        "model_accuracy": round(float(bt["correct"].mean()), 4),
        "model_log_loss": round(float(bt["log_loss"].mean()), 4),
        "model_rps": round(float(bt["rps"].mean()), 4),
        "baseline_accuracy": round(float(baseline["correct"].mean()), 4),
        "baseline_log_loss": round(float(baseline["log_loss"].mean()), 4),
        "baseline_rps": round(float(baseline["rps"].mean()), 4),
        "notes": (
            "Walk-forward backtest: the model is refit using only matches strictly "
            "before each prediction, so this reflects what the model would have "
            "known at the time. RPS (Ranked Probability Score) is the standard "
            "football-forecasting metric; lower is better. Baseline uses only "
            "home-field base rates with no team-specific skill."
        ),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {OUT_PATH}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
