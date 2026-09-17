export interface TeamRating {
  team: string;
  attack: number;
  defense: number;
  net_rating: number;
  current_season_matches: number;
  thin_data: boolean;
  form_last5: string[];
  goals_scored_per_game: number | null;
  goals_conceded_per_game: number | null;
}

export interface FixturePrediction {
  date: string;
  home_team: string;
  away_team: string;
  home_win: number;
  draw: number;
  away_win: number;
  expected_home_goals: number;
  expected_away_goals: number;
  over_2_5: number;
  under_2_5: number;
  btts_yes: number;
  btts_no: number;
  home_thin_data: boolean;
  away_thin_data: boolean;
}

export interface BacktestSummary {
  generated_at: string;
  date_range: string;
  n_matches: number;
  model_accuracy: number;
  model_log_loss: number;
  model_rps: number;
  baseline_accuracy: number;
  baseline_log_loss: number;
  baseline_rps: number;
  notes: string;
}

export interface BetEvaluation {
  outcome: string;
  model_prob: number;
  market_prob_devigged: number;
  decimal_odds: number;
  edge: number;
  kelly_stake_pct: number;
}

export interface LiveScore {
  fixture_id: number | null;
  kickoff: string | null;
  status_short: string | null;
  status_label: string | null;
  home_team: string | null;
  away_team: string | null;
  home_goals: number | null;
  away_goals: number | null;
}
