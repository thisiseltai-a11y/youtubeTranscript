import type { BacktestSummary } from "@/lib/types";
import { pct } from "@/lib/format";

function StatBlock({
  label,
  model,
  baseline,
  higherIsBetter,
}: {
  label: string;
  model: string;
  baseline: string;
  higherIsBetter: boolean;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4 shadow-sm">
      <div className="text-xs font-semibold tracking-wide text-muted uppercase">{label}</div>
      <div className="mt-1.5 flex items-baseline gap-2">
        <span className="text-2xl font-bold text-brand">{model}</span>
        <span className="text-xs text-muted">{higherIsBetter ? "higher is better" : "lower is better"}</span>
      </div>
      <div className="mt-1 text-sm text-muted">vs. naive baseline: {baseline}</div>
    </div>
  );
}

export function HowItWorks({ summary }: { summary: BacktestSummary | null }) {
  return (
    <section id="how-it-works" className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <h2 className="text-xl font-semibold tracking-tight">How this works</h2>
      <div className="mt-3 max-w-3xl space-y-3 text-sm leading-relaxed text-muted">
        <p>
          This is a <strong className="text-foreground">statistical model, not a guarantee</strong>. It
          estimates match probabilities from a Dixon-Coles Poisson model fit to English Premier League
          results — each team gets an attack and defense rating from historical goals, adjusted for home
          advantage and recent form. It does not know about injuries, tactics, weather, or anything that
          hasn&apos;t shown up in the scoreline data yet.
        </p>
        <p>
          Numbers below are from a <strong className="text-foreground">walk-forward backtest</strong>: at
          each point in time, the model is refit using only matches that happened before it, then scored
          on what actually happened next — the same information you&apos;d have had in real time, no
          hindsight.
        </p>
      </div>

      {summary ? (
        <>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatBlock
              label="Accuracy"
              model={pct(summary.model_accuracy)}
              baseline={pct(summary.baseline_accuracy)}
              higherIsBetter
            />
            <StatBlock
              label="RPS (ranked probability score)"
              model={summary.model_rps.toFixed(3)}
              baseline={summary.baseline_rps.toFixed(3)}
              higherIsBetter={false}
            />
            <StatBlock
              label="Log loss"
              model={summary.model_log_loss.toFixed(3)}
              baseline={summary.baseline_log_loss.toFixed(3)}
              higherIsBetter={false}
            />
          </div>
          <p className="mt-3 text-xs text-muted">
            Backtested on {summary.n_matches.toLocaleString()} matches ({summary.date_range}). Baseline
            uses only home-field base rates, no team-specific skill.
          </p>
        </>
      ) : (
        <p className="mt-6 text-sm text-muted">Backtest summary unavailable right now.</p>
      )}

      <p className="mt-6 max-w-3xl text-sm text-muted">
        This tool does not take bets or handle money. It shows probabilities and, if you provide odds
        yourself, the math for comparing them — what you do with that is your decision and your risk.
        Past performance of the model does not guarantee future results.
      </p>
    </section>
  );
}
