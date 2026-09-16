"""
backtest.py

Walk-forward backtest for the Dixon-Coles model.

Critical rule: the model is refit at each step using ONLY matches that
happened strictly before the match(es) being predicted. No look-ahead bias.
This simulates what you'd actually know the morning of a matchday.

Metrics reported:
  - Accuracy: did the highest-probability outcome happen?
  - Log loss: penalizes confident wrong predictions harder (lower = better)
  - RPS (Ranked Probability Score): the standard football-forecasting metric.
    Unlike log loss, RPS respects that H/D/A are ordered outcomes (a model
    that says "probably a draw" when it's actually a home win should be
    penalized less than one that said "definitely away win"). Lower = better.
  - Baseline comparison: a naive model using only home-field base rates
    (no team-specific info) — your model needs to beat this to be worth anything.
"""
import numpy as np
import pandas as pd
from poisson_model import DixonColesModel


def rps(probs, outcome_idx, n_outcomes=3):
    """Ranked Probability Score for one prediction. probs ordered [home_win, draw, away_win]."""
    cum_probs = np.cumsum(probs)
    cum_actual = np.zeros(n_outcomes)
    cum_actual[outcome_idx:] = 1.0
    return np.sum((cum_probs - cum_actual) ** 2) / (n_outcomes - 1)


def walk_forward_backtest(matches: pd.DataFrame, min_train_matches=380, xi=0.0018,
                           refit_every_matches=20, train_window_matches=1200):
    """
    matches: full historical DataFrame, sorted by date ascending.
    min_train_matches: don't start predicting until the model has at least
        this many historical matches to train on (~1 season).
    refit_every_matches: only refit the model after this many new matches have
        been played, instead of before every single match — keeps runtime
        reasonable. Predictions still only ever use data strictly before the
        matches being predicted (no look-ahead).
    train_window_matches: rolling window cap on training data (most recent N
        matches) — keeps team-count/runtime bounded and reflects that a team's
        true strength drifts over multiple seasons, so very old matches add
        little and mostly cost fitting time.
    """
    matches = matches.sort_values("date").reset_index(drop=True)
    unique_dates = sorted(matches["date"].unique())

    results = []
    model = None
    matches_since_fit = refit_every_matches  # force fit on first eligible date

    for d in unique_dates:
        train_full = matches[matches["date"] < d]
        if len(train_full) < min_train_matches:
            continue
        train = train_full.tail(train_window_matches)

        todays_matches = matches[matches["date"] == d]

        if model is None or matches_since_fit >= refit_every_matches:
            model = DixonColesModel(xi=xi).fit(train, ref_date=d)
            matches_since_fit = 0

        for _, row in todays_matches.iterrows():
            h, a = row["home_team"], row["away_team"]
            if h not in model.attack_ or a not in model.attack_:
                continue  # newly promoted team with no history yet — skip
            probs = model.match_probabilities(h, a)
            p_vec = [probs["home_win"], probs["draw"], probs["away_win"]]

            if row["home_goals"] > row["away_goals"]:
                actual = "H"
                outcome_idx = 0
            elif row["home_goals"] == row["away_goals"]:
                actual = "D"
                outcome_idx = 1
            else:
                actual = "A"
                outcome_idx = 2

            predicted = ["H", "D", "A"][int(np.argmax(p_vec))]
            eps = 1e-10
            log_loss = -np.log(max(p_vec[outcome_idx], eps))

            results.append({
                "date": d, "home_team": h, "away_team": a,
                "p_home": p_vec[0], "p_draw": p_vec[1], "p_away": p_vec[2],
                "actual": actual, "predicted": predicted,
                "correct": actual == predicted,
                "log_loss": log_loss,
                "rps": rps(p_vec, outcome_idx),
            })

        matches_since_fit += len(todays_matches)

    return pd.DataFrame(results)


def baseline_comparison(backtest_df: pd.DataFrame, full_matches: pd.DataFrame):
    """Naive baseline: constant probabilities from home-field base rates only (no team skill)."""
    train_period = full_matches[full_matches["date"] < backtest_df["date"].min()]
    outcomes = np.where(train_period.home_goals > train_period.away_goals, "H",
                np.where(train_period.home_goals == train_period.away_goals, "D", "A"))
    base_rates = pd.Series(outcomes).value_counts(normalize=True)
    p_base = [base_rates.get("H", 0.45), base_rates.get("D", 0.25), base_rates.get("A", 0.30)]

    rows = []
    for _, row in backtest_df.iterrows():
        outcome_idx = {"H": 0, "D": 1, "A": 2}[row["actual"]]
        eps = 1e-10
        rows.append({
            "log_loss": -np.log(max(p_base[outcome_idx], eps)),
            "rps": rps(p_base, outcome_idx),
            "correct": (["H", "D", "A"][int(np.argmax(p_base))] == row["actual"]),
        })
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame, label: str):
    print(f"{label:>20} | n={len(df):4d} | accuracy={df['correct'].mean():.3f} | "
          f"log_loss={df['log_loss'].mean():.4f} | RPS={df['rps'].mean():.4f}")


if __name__ == "__main__":
    from data_loader import load_all_seasons
    df = load_all_seasons()
    print(f"Loaded {len(df)} matches ({df.date.min().date()} to {df.date.max().date()})")
    print("Running walk-forward backtest (this refits the model periodically — may take ~1-2 min)...\n")

    bt = walk_forward_backtest(df, min_train_matches=380, xi=0.0018, refit_every_matches=20)
    baseline = baseline_comparison(bt, df)

    print(f"Backtested on {len(bt)} matches (holding out the first season to build initial ratings)\n")
    summarize(bt, "Dixon-Coles model")
    summarize(baseline, "Naive baseline")

    bt.to_csv("backtest_results.csv", index=False)
    print("\nSaved full match-by-match results to backtest_results.csv")
