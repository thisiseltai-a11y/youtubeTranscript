"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { evaluateBet } from "@/lib/api";
import type { BetEvaluation, FixturePrediction } from "@/lib/types";
import { pct, signedPct } from "@/lib/format";

const CUSTOM = "__custom__";

function NumberField({
  label,
  value,
  onChange,
  step = 0.01,
  min,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  step?: number;
  min?: number;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-neutral-500">
      {label}
      <input
        type="number"
        inputMode="decimal"
        step={step}
        min={min}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-black/10 bg-white px-2 py-1.5 text-sm text-neutral-900 dark:border-white/10 dark:bg-neutral-900 dark:text-white"
      />
    </label>
  );
}

export function BetEvaluator({ fixtures }: { fixtures: FixturePrediction[] }) {
  const [selected, setSelected] = useState<string>(fixtures.length ? "0" : CUSTOM);
  const [prevSelected, setPrevSelected] = useState(selected);

  const initialFixture = fixtures[0];
  const [homeProb, setHomeProb] = useState(initialFixture ? initialFixture.home_win.toFixed(4) : "0.45");
  const [drawProb, setDrawProb] = useState(initialFixture ? initialFixture.draw.toFixed(4) : "0.27");
  const [awayProb, setAwayProb] = useState(initialFixture ? initialFixture.away_win.toFixed(4) : "0.28");

  const [homeOdds, setHomeOdds] = useState("1.95");
  const [drawOdds, setDrawOdds] = useState("3.60");
  const [awayOdds, setAwayOdds] = useState("4.20");

  const [kellyFrac, setKellyFrac] = useState("0.25");
  const [minEdge, setMinEdge] = useState("0.02");

  const [results, setResults] = useState<BetEvaluation[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  // Prefill model probabilities from the selected fixture. Done during render
  // (the pattern React recommends for "adjust state when a prop changes")
  // rather than in an effect, since it only needs to run once per selection.
  if (selected !== prevSelected) {
    setPrevSelected(selected);
    if (selected !== CUSTOM) {
      const f = fixtures[Number(selected)];
      if (f) {
        setHomeProb(f.home_win.toFixed(4));
        setDrawProb(f.draw.toFixed(4));
        setAwayProb(f.away_win.toFixed(4));
      }
    }
  }

  const payload = useMemo(() => {
    const hp = parseFloat(homeProb);
    const dp = parseFloat(drawProb);
    const ap = parseFloat(awayProb);
    const ho = parseFloat(homeOdds);
    const doo = parseFloat(drawOdds);
    const ao = parseFloat(awayOdds);
    const kf = parseFloat(kellyFrac);
    const me = parseFloat(minEdge);
    if ([hp, dp, ap, ho, doo, ao, kf, me].some((v) => Number.isNaN(v))) return null;
    if (ho <= 1 || doo <= 1 || ao <= 1) return null;
    return {
      model_probs: { home_win: hp, draw: dp, away_win: ap },
      market_decimal_odds: { home_win: ho, draw: doo, away_win: ao },
      kelly_frac: kf,
      min_edge: me,
    };
  }, [homeProb, drawProb, awayProb, homeOdds, drawOdds, awayOdds, kellyFrac, minEdge]);

  useEffect(() => {
    if (!payload) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      startTransition(async () => {
        try {
          const r = await evaluateBet(payload);
          if (!cancelled) {
            setResults(r);
            setError(null);
          }
        } catch (e) {
          if (!cancelled) setError(e instanceof Error ? e.message : "Failed to evaluate");
        }
      });
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [payload]);

  return (
    <section id="evaluator" className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <h2 className="text-xl font-semibold">Bet evaluator</h2>
      <p className="mt-1 max-w-2xl text-sm text-neutral-500">
        Pick a fixture (or enter your own probabilities), enter the decimal odds you&apos;re
        seeing, and see the model&apos;s edge and a fractional-Kelly stake suggestion. Nothing
        here places a bet — it&apos;s just the math.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <label className="flex flex-col gap-1 text-xs text-neutral-500">
            Match
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="rounded-md border border-black/10 bg-white px-2 py-1.5 text-sm text-neutral-900 dark:border-white/10 dark:bg-neutral-900 dark:text-white"
            >
              {fixtures.map((f, i) => (
                <option key={`${f.home_team}-${f.away_team}`} value={i}>
                  {f.home_team} vs {f.away_team}
                </option>
              ))}
              <option value={CUSTOM}>Custom probabilities</option>
            </select>
          </label>

          <div>
            <div className="mb-1 text-xs font-medium text-neutral-500">Model probabilities</div>
            <div className="grid grid-cols-3 gap-2">
              <NumberField label="Home win" value={homeProb} onChange={setHomeProb} step={0.001} min={0} />
              <NumberField label="Draw" value={drawProb} onChange={setDrawProb} step={0.001} min={0} />
              <NumberField label="Away win" value={awayProb} onChange={setAwayProb} step={0.001} min={0} />
            </div>
          </div>

          <div>
            <div className="mb-1 text-xs font-medium text-neutral-500">Market decimal odds</div>
            <div className="grid grid-cols-3 gap-2">
              <NumberField label="Home win" value={homeOdds} onChange={setHomeOdds} min={1.01} />
              <NumberField label="Draw" value={drawOdds} onChange={setDrawOdds} min={1.01} />
              <NumberField label="Away win" value={awayOdds} onChange={setAwayOdds} min={1.01} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <NumberField label="Kelly fraction" value={kellyFrac} onChange={setKellyFrac} step={0.05} min={0} />
            <NumberField label="Min. edge to flag" value={minEdge} onChange={setMinEdge} step={0.01} min={0} />
          </div>
        </div>

        <div className="rounded-xl border border-black/10 p-4 dark:border-white/10">
          <div className="mb-3 text-xs font-medium text-neutral-500">
            {isPending ? "Evaluating…" : "Results"}
          </div>
          {!payload && (
            <p className="text-sm text-neutral-500">
              Enter valid probabilities and odds (odds must be greater than 1) to see results.
            </p>
          )}
          {payload && error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
          {payload && !error && results && results.length === 0 && (
            <p className="text-sm text-neutral-500">
              No outcome clears the minimum edge threshold — the market looks fair or better here.
            </p>
          )}
          {payload && !error && results && results.length > 0 && (
            <div className="space-y-3">
              {results.map((b) => (
                <div key={b.outcome} className="rounded-lg border border-black/10 p-3 text-sm dark:border-white/10">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize">{b.outcome.replace("_", " ")}</span>
                    <span
                      className={
                        b.edge >= 0
                          ? "font-semibold text-emerald-600 dark:text-emerald-400"
                          : "font-semibold text-red-600 dark:text-red-400"
                      }
                    >
                      {signedPct(b.edge)} edge
                    </span>
                  </div>
                  <div className="mt-1 grid grid-cols-2 gap-1 text-xs text-neutral-500">
                    <div>Model: {pct(b.model_prob)}</div>
                    <div>Market (de-vigged): {pct(b.market_prob_devigged)}</div>
                    <div>Odds: {b.decimal_odds.toFixed(2)}</div>
                    <div>Suggested stake: {pct(b.kelly_stake_pct, 2)} of bankroll</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
