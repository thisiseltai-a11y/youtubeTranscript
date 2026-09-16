"use client";

import { useState } from "react";
import { evaluateBet } from "@/lib/api";
import { explainBtts, explainResult, explainTotalGoals } from "@/lib/explain";
import { fmtDate, pct } from "@/lib/format";
import type { BetEvaluation, FixturePrediction, TeamRating } from "@/lib/types";
import { ThinDataBadge } from "./ThinDataBadge";

interface Outcome {
  key: string;
  label: string;
  prob: number;
}

interface Market {
  title: string;
  outcomes: Outcome[];
  explanation: string;
}

function OddsChecker({ outcomes }: { outcomes: Outcome[] }) {
  const [odds, setOdds] = useState<Record<string, string>>({});
  const [results, setResults] = useState<BetEvaluation[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function check() {
    const marketOdds: Record<string, number> = {};
    for (const o of outcomes) {
      const v = parseFloat(odds[o.key] ?? "");
      if (!Number.isFinite(v) || v <= 1) {
        setError("Enter odds greater than 1.00 for every outcome.");
        return;
      }
      marketOdds[o.key] = v;
    }
    setError(null);
    setLoading(true);
    try {
      const modelProbs: Record<string, number> = {};
      outcomes.forEach((o) => {
        modelProbs[o.key] = o.prob;
      });
      const r = await evaluateBet({ model_probs: modelProbs, market_decimal_odds: marketOdds });
      setResults(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to check odds");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-2 rounded-md bg-neutral-50 p-2 dark:bg-white/5">
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${outcomes.length}, minmax(0,1fr))` }}>
        {outcomes.map((o) => (
          <label key={o.key} className="flex flex-col gap-0.5 text-[11px] text-neutral-500">
            {o.label} odds
            <input
              type="number"
              inputMode="decimal"
              step={0.01}
              min={1.01}
              value={odds[o.key] ?? ""}
              onChange={(e) => setOdds((s) => ({ ...s, [o.key]: e.target.value }))}
              className="rounded border border-black/10 bg-white px-1.5 py-1 text-xs text-neutral-900 dark:border-white/10 dark:bg-neutral-900 dark:text-white"
            />
          </label>
        ))}
      </div>
      <button
        type="button"
        onClick={check}
        disabled={loading}
        className="mt-2 rounded-md border border-black/10 px-2 py-1 text-xs font-medium hover:bg-black/5 disabled:opacity-50 dark:border-white/10 dark:hover:bg-white/10"
      >
        {loading ? "Checking…" : "Check for value"}
      </button>
      {error && <p className="mt-1 text-xs text-red-600 dark:text-red-400">{error}</p>}
      {results && (
        <div className="mt-2 space-y-1">
          {results.length === 0 && (
            <p className="text-xs text-neutral-500">No value found — these odds look fair or better.</p>
          )}
          {results.map((b) => (
            <div key={b.outcome} className="text-xs">
              <span className="font-medium capitalize">{b.outcome.replace(/_/g, " ")}</span>:{" "}
              <span
                className={
                  b.edge >= 0
                    ? "font-medium text-emerald-600 dark:text-emerald-400"
                    : "font-medium text-red-600 dark:text-red-400"
                }
              >
                {b.edge >= 0 ? "+" : ""}
                {(b.edge * 100).toFixed(1)}% value
              </span>{" "}
              — suggested {pct(b.kelly_stake_pct, 2)} of bankroll
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MarketBlock({ market }: { market: Market }) {
  const [showWhy, setShowWhy] = useState(false);
  const [showOdds, setShowOdds] = useState(false);

  return (
    <div className="rounded-lg border border-black/10 p-3 dark:border-white/10">
      <div className="text-xs font-medium text-neutral-500">{market.title}</div>
      <div
        className="mt-2 grid gap-2"
        style={{ gridTemplateColumns: `repeat(${market.outcomes.length}, minmax(0,1fr))` }}
      >
        {market.outcomes.map((o) => (
          <div key={o.key} className="rounded-md bg-neutral-50 px-2 py-1.5 text-center dark:bg-white/5">
            <div className="truncate text-[11px] text-neutral-500">{o.label}</div>
            <div className="text-sm font-semibold">{pct(o.prob)}</div>
          </div>
        ))}
      </div>
      <div className="mt-2 flex gap-3 text-xs">
        <button
          type="button"
          onClick={() => setShowWhy((v) => !v)}
          className="text-neutral-500 underline decoration-dotted underline-offset-2 hover:text-neutral-700 dark:hover:text-neutral-300"
        >
          {showWhy ? "Hide reason" : "Why?"}
        </button>
        <button
          type="button"
          onClick={() => setShowOdds((v) => !v)}
          className="text-neutral-500 underline decoration-dotted underline-offset-2 hover:text-neutral-700 dark:hover:text-neutral-300"
        >
          {showOdds ? "Hide odds check" : "Check my sportsbook odds"}
        </button>
      </div>
      {showWhy && <p className="mt-2 text-xs text-neutral-600 dark:text-neutral-300">{market.explanation}</p>}
      {showOdds && <OddsChecker outcomes={market.outcomes} />}
    </div>
  );
}

export function MatchCard({
  f,
  homeRating,
  awayRating,
}: {
  f: FixturePrediction;
  homeRating?: TeamRating;
  awayRating?: TeamRating;
}) {
  const markets: Market[] = [
    {
      title: "Match result",
      outcomes: [
        { key: "home_win", label: f.home_team, prob: f.home_win },
        { key: "draw", label: "Draw", prob: f.draw },
        { key: "away_win", label: f.away_team, prob: f.away_win },
      ],
      explanation: explainResult(f, homeRating, awayRating),
    },
    {
      title: "Total goals",
      outcomes: [
        { key: "over_2_5", label: "Over 2.5", prob: f.over_2_5 },
        { key: "under_2_5", label: "Under 2.5", prob: f.under_2_5 },
      ],
      explanation: explainTotalGoals(f),
    },
    {
      title: "Both teams to score",
      outcomes: [
        { key: "btts_yes", label: "Yes", prob: f.btts_yes },
        { key: "btts_no", label: "No", prob: f.btts_no },
      ],
      explanation: explainBtts(f),
    },
  ];

  return (
    <div className="rounded-xl border border-black/10 p-4 dark:border-white/10">
      <div className="text-xs text-neutral-500">{fmtDate(f.date)}</div>
      <div className="mt-1 flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-medium">{f.home_team}</div>
          {f.home_thin_data && (
            <div className="mt-1">
              <ThinDataBadge />
            </div>
          )}
        </div>
        <div className="shrink-0 text-xs text-neutral-400">vs</div>
        <div className="min-w-0 text-right">
          <div className="truncate font-medium">{f.away_team}</div>
          {f.away_thin_data && (
            <div className="mt-1 flex justify-end">
              <ThinDataBadge />
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {markets.map((m) => (
          <MarketBlock key={m.title} market={m} />
        ))}
      </div>
    </div>
  );
}
