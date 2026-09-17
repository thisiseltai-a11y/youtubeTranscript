"use client";

import { useState } from "react";
import { evaluateBet } from "@/lib/api";
import { explainBtts, explainResult, explainTotalGoals, type Explanation } from "@/lib/explain";
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
  explanation: Explanation;
}

function WhyPanel({ explanation }: { explanation: Explanation }) {
  return (
    <div className="mt-2.5 space-y-1.5 rounded-lg bg-background p-2.5">
      {explanation.facts.map((f) => (
        <div key={f.label} className="flex items-center justify-between gap-3 text-xs">
          <span className="text-muted">{f.label}</span>
          <span className="font-semibold">{f.value}</span>
        </div>
      ))}
      {explanation.note && (
        <div
          className="mt-1.5 rounded-md px-2 py-1.5 text-[11px] leading-snug"
          style={{ backgroundColor: "var(--warning-bg)", color: "var(--warning-fg)" }}
        >
          {explanation.note}
        </div>
      )}
    </div>
  );
}

function OutcomeCell({ o, isLeading }: { o: Outcome; isLeading: boolean }) {
  return (
    <div className="min-w-0 rounded-lg bg-background px-2.5 py-2 text-center">
      <div className="truncate text-[11px] text-muted">{o.label}</div>
      <div className={isLeading ? "text-base font-bold text-brand" : "text-base font-bold"}>
        {pct(o.prob)}
      </div>
      <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-border">
        <div
          className={isLeading ? "h-full rounded-full bg-brand" : "h-full rounded-full bg-muted/60"}
          style={{ width: `${Math.max(o.prob * 100, 3)}%` }}
        />
      </div>
    </div>
  );
}

function PillButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? "rounded-full bg-brand-soft px-2.5 py-1 text-xs font-medium text-brand"
          : "rounded-full bg-background px-2.5 py-1 text-xs font-medium text-muted transition-colors hover:text-foreground"
      }
    >
      {children}
    </button>
  );
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
    <div className="mt-3 rounded-lg bg-background p-2.5">
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${outcomes.length}, minmax(0,1fr))` }}>
        {outcomes.map((o) => (
          <label key={o.key} className="flex flex-col gap-0.5 text-[11px] text-muted">
            {o.label} odds
            <input
              type="number"
              inputMode="decimal"
              step={0.01}
              min={1.01}
              value={odds[o.key] ?? ""}
              onChange={(e) => setOdds((s) => ({ ...s, [o.key]: e.target.value }))}
              className="rounded-md border border-border bg-surface px-1.5 py-1 text-xs text-foreground"
            />
          </label>
        ))}
      </div>
      <button
        type="button"
        onClick={check}
        disabled={loading}
        className="mt-2 rounded-md bg-brand px-2.5 py-1 text-xs font-semibold text-brand-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {loading ? "Checking…" : "Check for value"}
      </button>
      {error && <p className="mt-1 text-xs text-negative">{error}</p>}
      {results && (
        <div className="mt-2 space-y-1">
          {results.length === 0 && (
            <p className="text-xs text-muted">No value found — these odds look fair or better.</p>
          )}
          {results.map((b) => (
            <div key={b.outcome} className="text-xs">
              <span className="font-medium capitalize">{b.outcome.replace(/_/g, " ")}</span>:{" "}
              <span className={b.edge >= 0 ? "font-semibold text-positive" : "font-semibold text-negative"}>
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
  const maxProb = Math.max(...market.outcomes.map((o) => o.prob));

  return (
    <div className="rounded-xl border border-border bg-surface p-3">
      <div className="text-xs font-medium text-muted">{market.title}</div>
      <div
        className="mt-2 grid gap-2"
        style={{ gridTemplateColumns: `repeat(${market.outcomes.length}, minmax(0,1fr))` }}
      >
        {market.outcomes.map((o) => (
          <OutcomeCell key={o.key} o={o} isLeading={o.prob === maxProb} />
        ))}
      </div>
      <div className="mt-2.5 flex gap-2">
        <PillButton active={showWhy} onClick={() => setShowWhy((v) => !v)}>
          {showWhy ? "Hide reason" : "Why?"}
        </PillButton>
        <PillButton active={showOdds} onClick={() => setShowOdds((v) => !v)}>
          {showOdds ? "Hide odds check" : "Check my sportsbook odds"}
        </PillButton>
      </div>
      {showWhy && <WhyPanel explanation={market.explanation} />}
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
    <div className="rounded-2xl border border-border bg-surface p-4 shadow-sm">
      <div className="text-xs font-medium text-muted">{fmtDate(f.date)}</div>
      <div className="mt-1.5 flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-semibold">{f.home_team}</div>
          {f.home_thin_data && (
            <div className="mt-1">
              <ThinDataBadge />
            </div>
          )}
        </div>
        <div className="shrink-0 text-xs font-medium text-muted">vs</div>
        <div className="min-w-0 text-right">
          <div className="truncate font-semibold">{f.away_team}</div>
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
