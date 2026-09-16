"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { evaluateBet } from "@/lib/api";
import type { BetEvaluation, FixturePrediction } from "@/lib/types";
import { pct, signedPct } from "@/lib/format";

const CUSTOM = "__custom__";
const DEFAULT_KELLY_FRAC = "0.25";
const DEFAULT_MIN_EDGE = "0.02";

function NumberField({
  label,
  value,
  onChange,
  step = 0.01,
  min,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  step?: number;
  min?: number;
  disabled?: boolean;
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
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-black/10 bg-white px-2 py-1.5 text-sm text-neutral-900 disabled:cursor-not-allowed disabled:bg-neutral-100 disabled:text-neutral-400 dark:border-white/10 dark:bg-neutral-900 dark:text-white dark:disabled:bg-white/5 dark:disabled:text-neutral-500"
      />
    </label>
  );
}

function PredictionChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-black/10 px-2 py-1.5 text-center dark:border-white/10">
      <div className="text-xs text-neutral-500">{label}</div>
      <div className="text-sm font-semibold">{value}</div>
    </div>
  );
}

export function BetEvaluator({ fixtures }: { fixtures: FixturePrediction[] }) {
  const [selected, setSelected] = useState<string>(fixtures.length ? "0" : CUSTOM);
  const [prevSelected, setPrevSelected] = useState(selected);
  const isCustom = selected === CUSTOM;

  const initialFixture = fixtures[0];
  const [homeProb, setHomeProb] = useState(initialFixture ? initialFixture.home_win.toFixed(4) : "0.45");
  const [drawProb, setDrawProb] = useState(initialFixture ? initialFixture.draw.toFixed(4) : "0.27");
  const [awayProb, setAwayProb] = useState(initialFixture ? initialFixture.away_win.toFixed(4) : "0.28");

  const [homeOdds, setHomeOdds] = useState("1.95");
  const [drawOdds, setDrawOdds] = useState("3.60");
  const [awayOdds, setAwayOdds] = useState("4.20");

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [kellyFrac, setKellyFrac] = useState(DEFAULT_KELLY_FRAC);
  const [minEdge, setMinEdge] = useState(DEFAULT_MIN_EDGE);

  const [results, setResults] = useState<BetEvaluation[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  // Prefill the prediction from the selected fixture. Done during render
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
        Pick a match, type in the odds your sportsbook is offering, and see whether our
        prediction thinks there&apos;s value. Nothing here places a bet — it&apos;s just the
        math.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <label className="flex flex-col gap-1 text-xs text-neutral-500">
            1. Pick a match
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
              <option value={CUSTOM}>Enter my own prediction instead</option>
            </select>
          </label>

          <div>
            <div className="mb-1 text-xs font-medium text-neutral-500">
              {isCustom ? "Your prediction (win probabilities)" : "Our prediction for this match"}
            </div>
            {isCustom ? (
              <div className="grid grid-cols-3 gap-2">
                <NumberField label="Home win" value={homeProb} onChange={setHomeProb} step={0.001} min={0} />
                <NumberField label="Draw" value={drawProb} onChange={setDrawProb} step={0.001} min={0} />
                <NumberField label="Away win" value={awayProb} onChange={setAwayProb} step={0.001} min={0} />
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                <PredictionChip label="Home win" value={pct(parseFloat(homeProb))} />
                <PredictionChip label="Draw" value={pct(parseFloat(drawProb))} />
                <PredictionChip label="Away win" value={pct(parseFloat(awayProb))} />
              </div>
            )}
          </div>

          <div>
            <div className="mb-1 text-xs font-medium text-neutral-500">
              2. Odds you&apos;re seeing at your sportsbook
            </div>
            <p className="mb-2 text-xs text-neutral-500">
              Use decimal odds (e.g. 1.95, not +95 or 20/21) — most sportsbook apps let you
              switch the odds format in settings if you only see American or fractional odds.
            </p>
            <div className="grid grid-cols-3 gap-2">
              <NumberField label="Home win" value={homeOdds} onChange={setHomeOdds} min={1.01} />
              <NumberField label="Draw" value={drawOdds} onChange={setDrawOdds} min={1.01} />
              <NumberField label="Away win" value={awayOdds} onChange={setAwayOdds} min={1.01} />
            </div>
          </div>

          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className="text-xs font-medium text-neutral-500 underline decoration-dotted underline-offset-2 hover:text-neutral-700 dark:hover:text-neutral-300"
            >
              {showAdvanced ? "Hide" : "Show"} advanced settings
            </button>
            {showAdvanced && (
              <div className="mt-2 grid grid-cols-2 gap-2">
                <NumberField
                  label="Kelly fraction (bet sizing caution — lower is more conservative)"
                  value={kellyFrac}
                  onChange={setKellyFrac}
                  step={0.05}
                  min={0}
                />
                <NumberField
                  label="Minimum edge to show a result"
                  value={minEdge}
                  onChange={setMinEdge}
                  step={0.01}
                  min={0}
                />
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-black/10 p-4 dark:border-white/10">
          <div className="mb-3 text-xs font-medium text-neutral-500">
            {isPending ? "Evaluating…" : "Results"}
          </div>
          {!payload && (
            <p className="text-sm text-neutral-500">
              Enter valid odds (greater than 1.00) for all three outcomes to see results.
            </p>
          )}
          {payload && error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
          {payload && !error && results && results.length === 0 && (
            <p className="text-sm text-neutral-500">
              No value found here — the odds already look fair or better than our prediction, so
              there&apos;s nothing to flag.
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
                      {signedPct(b.edge)} value
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-neutral-500">
                    We think this happens {pct(b.model_prob)} of the time; the odds imply
                    {" "}{pct(b.market_prob_devigged)}.
                  </p>
                  <div className="mt-2 flex items-center justify-between rounded-md bg-neutral-50 px-2 py-1.5 text-xs dark:bg-white/5">
                    <span className="text-neutral-500">Odds: {b.decimal_odds.toFixed(2)}</span>
                    <span className="font-medium">
                      Suggested: {pct(b.kelly_stake_pct, 2)} of bankroll
                    </span>
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
