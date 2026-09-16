import type { BacktestSummary, BetEvaluation, FixturePrediction, LiveScore, TeamRating } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API error ${res.status} on ${path}`);
  }
  return res.json() as Promise<T>;
}

export function getRatings(): Promise<TeamRating[]> {
  return getJSON<TeamRating[]>("/ratings");
}

export function getFixtures(): Promise<FixturePrediction[]> {
  return getJSON<FixturePrediction[]>("/fixtures");
}

export function getBacktestSummary(): Promise<BacktestSummary> {
  return getJSON<BacktestSummary>("/backtest-summary");
}

export function getLiveScores(): Promise<LiveScore[]> {
  return getJSON<LiveScore[]>("/live-scores");
}

export interface EvaluateBetPayload {
  model_probs: Record<string, number>;
  market_decimal_odds: Record<string, number>;
  kelly_frac?: number;
  min_edge?: number;
}

export async function evaluateBet(payload: EvaluateBetPayload): Promise<BetEvaluation[]> {
  const res = await fetch(`${API_BASE}/evaluate-bet`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `API error ${res.status}`);
  }
  return res.json() as Promise<BetEvaluation[]>;
}
