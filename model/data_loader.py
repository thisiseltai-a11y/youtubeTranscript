"""
data_loader.py
Loads historical EPL match data (openfootball/football.json format) into a
clean pandas DataFrame ready for modeling.

Swap this out for your own feed (Sportradar, football-data.co.uk, etc.) —
the rest of the pipeline only needs: date, home_team, away_team, home_goals, away_goals.
"""
import json
import glob
import pandas as pd


def load_season_json(path: str) -> pd.DataFrame:
    with open(path) as f:
        data = json.load(f)
    rows = []
    for m in data["matches"]:
        score = m.get("score")
        if not score or "ft" not in score:
            continue  # unplayed fixture
        rows.append({
            "date": m["date"],
            "home_team": m["team1"],
            "away_team": m["team2"],
            "home_goals": score["ft"][0],
            "away_goals": score["ft"][1],
        })
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_all_seasons(data_dir: str = "data", pattern: str = "en1_*.json") -> pd.DataFrame:
    files = sorted(glob.glob(f"{data_dir}/{pattern}"))
    dfs = [load_season_json(f) for f in files]
    full = pd.concat(dfs, ignore_index=True)
    full = full.sort_values("date").reset_index(drop=True)
    return full


if __name__ == "__main__":
    df = load_all_seasons()
    print(f"Loaded {len(df)} matches, {df['date'].min().date()} to {df['date'].max().date()}")
    print(df.head())
    print(f"\nTeams: {sorted(set(df.home_team) | set(df.away_team))}")
