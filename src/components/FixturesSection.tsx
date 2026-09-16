import type { FixturePrediction } from "@/lib/types";
import { fmtDate, pct } from "@/lib/format";
import { ThinDataBadge } from "./ThinDataBadge";

function FixtureCard({ f }: { f: FixturePrediction }) {
  return (
    <div className="rounded-xl border border-black/10 p-4 dark:border-white/10">
      <div className="text-xs text-neutral-500">{fmtDate(f.date)}</div>

      <div className="mt-2 flex items-center justify-between gap-2">
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

      <div className="mt-4 flex overflow-hidden rounded-lg border border-black/10 text-xs dark:border-white/10">
        <div className="flex-1 border-r border-black/10 p-2 text-center dark:border-white/10">
          <div className="text-neutral-500">Home</div>
          <div className="font-semibold">{pct(f.home_win)}</div>
        </div>
        <div className="flex-1 border-r border-black/10 p-2 text-center dark:border-white/10">
          <div className="text-neutral-500">Draw</div>
          <div className="font-semibold">{pct(f.draw)}</div>
        </div>
        <div className="flex-1 p-2 text-center">
          <div className="text-neutral-500">Away</div>
          <div className="font-semibold">{pct(f.away_win)}</div>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-neutral-600 dark:text-neutral-300">
        <div>
          Expected goals: {f.expected_home_goals.toFixed(2)} – {f.expected_away_goals.toFixed(2)}
        </div>
        <div>Over 2.5: {pct(f.over_2_5)}</div>
        <div>BTTS: {pct(f.btts_yes)}</div>
        <div>Under 2.5: {pct(f.under_2_5)}</div>
      </div>
    </div>
  );
}

export function FixturesSection({ fixtures }: { fixtures: FixturePrediction[] }) {
  return (
    <section id="fixtures" className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <h2 className="text-xl font-semibold">Upcoming fixtures</h2>
      <p className="mt-1 text-sm text-neutral-500">
        Predictions for the next unplayed matchday. &quot;Limited data&quot; means the model has
        fewer than 6 matches of current-season history for that team.
      </p>

      {fixtures.length === 0 ? (
        <p className="mt-6 text-sm text-neutral-500">No upcoming fixtures found right now.</p>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {fixtures.map((f) => (
            <FixtureCard key={`${f.date}-${f.home_team}-${f.away_team}`} f={f} />
          ))}
        </div>
      )}
    </section>
  );
}
