"""
main.py

Ties the pipeline together end to end:
  1. Load all historical + current-season match data
  2. Fit the Dixon-Coles model using everything played so far
  3. Print team ratings
  4. Predict the next round of fixtures
  5. Show how to run a bet through the staking module once you have real odds

Run: python3 main.py
"""
import json
import glob
import pandas as pd
from data_loader import load_all_seasons
from poisson_model import DixonColesModel
from staking import evaluate_match_odds


def load_upcoming_fixtures(data_dir="data", pattern="en1_*.json"):
    """Pulls any unplayed fixtures out of the season files (no score yet)."""
    rows = []
    for f in sorted(glob.glob(f"{data_dir}/{pattern}")):
        with open(f) as fh:
            data = json.load(fh)
        for m in data["matches"]:
            if not m.get("score"):
                rows.append({"date": m["date"], "home_team": m["team1"], "away_team": m["team2"]})
    df = pd.DataFrame(rows)
    if len(df):
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
    return df


def main():
    matches = load_all_seasons()
    print(f"Loaded {len(matches)} played matches "
          f"({matches.date.min().date()} to {matches.date.max().date()})\n")

    model = DixonColesModel(xi=0.0018).fit(matches)
    print(f"Home advantage: {model.home_adv_:+.3f} (log scale) | "
          f"Low-score correction (rho): {model.rho_:+.3f}\n")

    print("=== Current team ratings (attack - defense, higher = stronger) ===")
    print(model.ratings_table().to_string(index=False))

    upcoming = load_upcoming_fixtures()
    if len(upcoming):
        next_date = upcoming["date"].min()
        next_round = upcoming[upcoming["date"] == next_date]
        print(f"\n=== Predictions for {next_date.date()} fixtures ===")
        for _, row in next_round.iterrows():
            h, a = row["home_team"], row["away_team"]
            if h not in model.attack_ or a not in model.attack_:
                continue
            p = model.match_probabilities(h, a)
            print(f"\n{h} vs {a}")
            print(f"  Win/Draw/Win:  H {p['home_win']:.1%}  D {p['draw']:.1%}  A {p['away_win']:.1%}")
            print(f"  Expected goals:  {h} {p['expected_home_goals']:.2f} - "
                  f"{p['expected_away_goals']:.2f} {a}")
            print(f"  Over/Under 2.5:  Over {p['over_2_5']:.1%}  Under {p['under_2_5']:.1%}")
            print(f"  BTTS:  Yes {p['btts_yes']:.1%}  No {p['btts_no']:.1%}")
    else:
        print("\nNo upcoming fixtures found in the local data files.")

    print("\n" + "=" * 60)
    print("To find betting edge, feed real sportsbook odds into staking.py:")
    print("=" * 60)
    print("""
  from staking import evaluate_match_odds

  model_probs = {"home_win": 0.55, "draw": 0.25, "away_win": 0.20}   # from model.match_probabilities()
  market_odds = {"home_win": 1.95, "draw": 3.60, "away_win": 4.20}   # decimal odds from your sportsbook

  bets = evaluate_match_odds(model_probs, market_odds, kelly_frac=0.25, min_edge=0.02)
  for b in bets:
      print(b)
""")


if __name__ == "__main__":
    main()
