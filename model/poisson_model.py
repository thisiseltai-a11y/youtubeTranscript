"""
poisson_model.py

Dixon-Coles bivariate Poisson model for soccer match outcomes.

Core idea:
  home_goals ~ Poisson(home_attack * away_defense * home_advantage)
  away_goals ~ Poisson(away_attack * home_defense)

Each team gets an attack rating and a defense rating, fit via maximum
likelihood on historical matches. Recent matches are weighted more heavily
(exponential time decay) so the model tracks current form, not just
season-long averages. The Dixon-Coles low-score correction (rho) fixes
Poisson's tendency to underrate 0-0/1-0/0-1/1-1 draws.

Reference: Dixon, M.J. and Coles, S.G. (1997), "Modelling Association
Football Scores and Inefficiencies in the Football Betting Market."
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson
from dataclasses import dataclass, field


def dc_adjustment(x, y, lam, mu, rho):
    """Dixon-Coles tau correction for low-scoring outcomes (0-0, 1-0, 0-1, 1-1)."""
    if x == 0 and y == 0:
        return 1 - lam * mu * rho
    elif x == 0 and y == 1:
        return 1 + lam * rho
    elif x == 1 and y == 0:
        return 1 + mu * rho
    elif x == 1 and y == 1:
        return 1 - rho
    return 1.0


@dataclass
class DixonColesModel:
    xi: float = 0.0018       # time-decay rate (per day); tune via backtest
    max_goals: int = 10      # scoreline grid cutoff
    l2_penalty: float = 0.15  # shrinkage toward league-average rating (see fit() docstring)
    teams_: list = field(default_factory=list)
    attack_: dict = field(default_factory=dict)
    defense_: dict = field(default_factory=dict)
    home_adv_: float = 0.0
    rho_: float = 0.0

    def _time_weights(self, dates, ref_date):
        days = (ref_date - dates).dt.days.values.astype(float)
        return np.exp(-self.xi * days)

    def fit(self, matches: pd.DataFrame, ref_date=None):
        """
        matches: DataFrame with columns date, home_team, away_team, home_goals, away_goals
        ref_date: matches are time-weighted relative to this date (defaults to max date in data,
                   i.e. "today" for the purposes of the fit — use the date you're predicting FROM).

        Regularization: an L2 penalty (self.l2_penalty) shrinks every team's attack/defense
        rating toward 0 (league average). This matters most for teams with very little
        history — e.g. a newly promoted side with 1-2 matches played — where an unregularized
        MLE fit can swing to the parameter bounds off pure small-sample noise (two early wins
        reading as an all-time-great defense). Established teams with a full season of data
        barely move; thin-data teams get pulled toward "assume average until proven otherwise,"
        which is the statistically honest default.
        """
        if ref_date is None:
            ref_date = matches["date"].max()
        teams = sorted(set(matches.home_team) | set(matches.away_team))
        self.teams_ = teams
        n = len(teams)
        idx = {t: i for i, t in enumerate(teams)}
        weights = self._time_weights(matches["date"], ref_date)

        hg = matches["home_goals"].values
        ag = matches["away_goals"].values
        hi = matches["home_team"].map(idx).values
        ai = matches["away_team"].map(idx).values

        def unpack(params):
            attack = params[:n]
            defense = params[n:2 * n]
            home_adv = params[2 * n]
            rho = params[2 * n + 1]
            return attack, defense, home_adv, rho

        def neg_log_likelihood(params):
            attack, defense, home_adv, rho = unpack(params)
            lam = np.exp(attack[hi] + defense[ai] + home_adv)  # expected home goals
            mu = np.exp(attack[ai] + defense[hi])              # expected away goals
            ll = poisson.logpmf(hg, lam) + poisson.logpmf(ag, mu)
            # Dixon-Coles low-score adjustment (only affects 0/1 scorelines)
            adj = np.array([
                dc_adjustment(h, a, l, m, rho)
                for h, a, l, m in zip(hg, ag, lam, mu)
            ])
            adj = np.clip(adj, 1e-6, None)
            ll = ll + np.log(adj)
            penalty = self.l2_penalty * (np.sum(attack ** 2) + np.sum(defense ** 2))
            return -np.sum(ll * weights) + penalty

        # init: attack=0, defense=0 (i.e. average team), home_adv=0.25, rho=0
        x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25], [0.0]])
        # Note: no explicit "mean attack = 0" constraint. The likelihood only depends on
        # attack[home]+defense[away] and attack[away]+defense[home], so attack/defense have
        # an arbitrary shared offset (attack += c, defense -= c leaves predictions unchanged).
        # That offset doesn't affect predicted probabilities, only raw rating interpretability,
        # so we drop the constraint and use unconstrained-style L-BFGS-B, which is far faster
        # than SLSQP with an equality constraint — this matters a lot for walk-forward backtests
        # that refit the model dozens of times.
        bounds = [(-3, 3)] * n + [(-3, 3)] * n + [(-2, 2)] + [(-1, 1)]

        res = minimize(neg_log_likelihood, x0, method="L-BFGS-B", bounds=bounds,
                        options={"maxiter": 150, "ftol": 1e-7})

        attack, defense, home_adv, rho = unpack(res.x)
        self.attack_ = dict(zip(teams, attack))
        self.defense_ = dict(zip(teams, defense))
        self.home_adv_ = float(home_adv)
        self.rho_ = float(rho)
        return self

    def expected_goals(self, home_team, away_team):
        a_h, d_h = self.attack_[home_team], self.defense_[home_team]
        a_a, d_a = self.attack_[away_team], self.defense_[away_team]
        lam = np.exp(a_h + d_a + self.home_adv_)  # home expected goals
        mu = np.exp(a_a + d_h)                    # away expected goals
        return lam, mu

    def scoreline_matrix(self, home_team, away_team):
        """Returns a (max_goals+1) x (max_goals+1) probability matrix: P[i,j] = P(home scores i, away scores j)."""
        lam, mu = self.expected_goals(home_team, away_team)
        gh = np.arange(0, self.max_goals + 1)
        ga = np.arange(0, self.max_goals + 1)
        ph = poisson.pmf(gh, lam)
        pa = poisson.pmf(ga, mu)
        mat = np.outer(ph, pa)
        # apply Dixon-Coles correction to the low-score cells
        for i in range(2):
            for j in range(2):
                mat[i, j] *= dc_adjustment(i, j, lam, mu, self.rho_)
        mat = mat / mat.sum()  # renormalize
        return mat

    def match_probabilities(self, home_team, away_team):
        """Returns a dict of derived market probabilities from the scoreline matrix."""
        mat = self.scoreline_matrix(home_team, away_team)
        n = mat.shape[0]
        home_win = np.tril(mat, -1).sum()
        draw = np.trace(mat)
        away_win = np.triu(mat, 1).sum()

        goals = np.add.outer(np.arange(n), np.arange(n))
        over_2_5 = mat[goals > 2].sum()
        under_2_5 = 1 - over_2_5

        btts_yes = mat[1:, 1:].sum()
        btts_no = 1 - btts_yes

        lam, mu = self.expected_goals(home_team, away_team)

        return {
            "home_win": home_win, "draw": draw, "away_win": away_win,
            "over_2_5": over_2_5, "under_2_5": under_2_5,
            "btts_yes": btts_yes, "btts_no": btts_no,
            "expected_home_goals": lam, "expected_away_goals": mu,
        }

    def ratings_table(self):
        rows = []
        for t in self.teams_:
            rows.append({
                "team": t,
                "attack": round(self.attack_[t], 3),
                "defense": round(self.defense_[t], 3),
                "net_rating": round(self.attack_[t] - self.defense_[t], 3),
            })
        return pd.DataFrame(rows).sort_values("net_rating", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    from data_loader import load_all_seasons
    df = load_all_seasons()
    model = DixonColesModel(xi=0.0018).fit(df)
    print("Home advantage (log-scale):", round(model.home_adv_, 3))
    print("Rho (low-score correction):", round(model.rho_, 3))
    print("\nTop 10 teams by net rating:")
    print(model.ratings_table().head(10).to_string(index=False))

    print("\nExample: Arsenal FC vs Chelsea FC")
    probs = model.match_probabilities("Arsenal FC", "Chelsea FC")
    for k, v in probs.items():
        print(f"  {k}: {v:.3f}")
