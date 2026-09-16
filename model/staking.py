"""
staking.py

Converts bookmaker odds to true (de-vigged) probabilities, compares them to
your model's probabilities to find edge, and sizes bets with the Kelly
criterion.

You'll need to plug in real odds yourself — from Sportradar (which you
already have API access to via HeyParlay), an odds-comparison API, or
manually from the sportsbook you bet at. This module doesn't fetch odds;
it's the math layer that sits on top of whatever odds feed you use.
"""
from dataclasses import dataclass


def american_to_decimal(odds: int) -> float:
    if odds > 0:
        return 1 + odds / 100
    return 1 + 100 / abs(odds)


def decimal_to_implied_prob(decimal_odds: float) -> float:
    return 1 / decimal_odds


def remove_vig(implied_probs: list) -> list:
    """
    Bookmaker odds always sum to >100% implied probability (the vig/juice).
    This rescales them proportionally so they sum to 1 — an estimate of the
    bookmaker's actual "true" probabilities, stripped of their margin.
    """
    total = sum(implied_probs)
    return [p / total for p in implied_probs]


def find_edge(model_prob: float, market_prob_devigged: float) -> float:
    """Positive = your model thinks the outcome is more likely than the market prices it."""
    return model_prob - market_prob_devigged


def kelly_fraction(model_prob: float, decimal_odds: float, fraction: float = 0.25) -> float:
    """
    Kelly criterion: what fraction of your bankroll to stake.

    Full Kelly = (b*p - q) / b, where:
      b = decimal_odds - 1 (net odds)
      p = your model's probability the bet wins
      q = 1 - p

    Full Kelly is mathematically optimal for long-run growth but has brutal
    variance and is highly sensitive to model error — if your probability
    estimate is even slightly too high, full Kelly overbets badly. `fraction`
    lets you bet a fraction of full Kelly (0.25-0.5 is standard practice) to
    cut variance a lot while still capturing most of the growth benefit.

    Returns 0 if there's no edge (negative Kelly = don't bet).
    """
    b = decimal_odds - 1
    q = 1 - model_prob
    full_kelly = (b * model_prob - q) / b
    return max(0.0, full_kelly * fraction)


@dataclass
class BetEvaluation:
    outcome: str
    model_prob: float
    market_prob_devigged: float
    decimal_odds: float
    edge: float
    kelly_stake_pct: float  # % of bankroll to stake (at chosen Kelly fraction)

    def __str__(self):
        return (f"{self.outcome:>10} | model={self.model_prob:.1%}  "
                f"market={self.market_prob_devigged:.1%}  "
                f"edge={self.edge:+.1%}  "
                f"odds={self.decimal_odds:.2f}  "
                f"stake={self.kelly_stake_pct:.2%} of bankroll")


def evaluate_match_odds(model_probs: dict, market_decimal_odds: dict, kelly_frac: float = 0.25,
                         min_edge: float = 0.02):
    """
    model_probs: e.g. {"home_win": 0.55, "draw": 0.25, "away_win": 0.20}
    market_decimal_odds: e.g. {"home_win": 1.90, "draw": 3.60, "away_win": 4.20}
    min_edge: don't bother flagging tiny edges likely to be noise, not signal.

    Returns a list of BetEvaluation, only for outcomes with edge >= min_edge.
    """
    outcomes = list(market_decimal_odds.keys())
    implied = [decimal_to_implied_prob(market_decimal_odds[o]) for o in outcomes]
    devigged = remove_vig(implied)

    bets = []
    for o, mp_market in zip(outcomes, devigged):
        mp_model = model_probs[o]
        edge = find_edge(mp_model, mp_market)
        if edge >= min_edge:
            stake = kelly_fraction(mp_model, market_decimal_odds[o], fraction=kelly_frac)
            bets.append(BetEvaluation(
                outcome=o, model_prob=mp_model, market_prob_devigged=mp_market,
                decimal_odds=market_decimal_odds[o], edge=edge, kelly_stake_pct=stake,
            ))
    return sorted(bets, key=lambda b: b.edge, reverse=True)


if __name__ == "__main__":
    # Example: your model likes the home win more than the market does
    model_probs = {"home_win": 0.55, "draw": 0.25, "away_win": 0.20}
    market_odds = {"home_win": 1.95, "draw": 3.60, "away_win": 4.20}  # decimal odds

    print("De-vigged market probabilities:")
    implied = [decimal_to_implied_prob(market_odds[o]) for o in market_odds]
    print(f"  Raw implied sums to {sum(implied):.1%} (the extra is the bookmaker's vig)")
    devigged = remove_vig(implied)
    for o, p in zip(market_odds, devigged):
        print(f"  {o}: {p:.1%}")

    print("\nBet evaluation:")
    bets = evaluate_match_odds(model_probs, market_odds, kelly_frac=0.25, min_edge=0.02)
    for b in bets:
        print(" ", b)
    if not bets:
        print("  No bets clear the minimum edge threshold.")
