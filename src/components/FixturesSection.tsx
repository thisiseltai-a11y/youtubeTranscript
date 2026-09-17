import type { FixturePrediction, TeamRating } from "@/lib/types";
import { MatchCard } from "./MatchCard";

export function FixturesSection({
  fixtures,
  ratings,
}: {
  fixtures: FixturePrediction[];
  ratings: TeamRating[];
}) {
  const ratingsByTeam = new Map(ratings.map((r) => [r.team, r]));

  return (
    <section id="fixtures" className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <h2 className="text-xl font-semibold tracking-tight">Upcoming matches</h2>
      <p className="mt-1 text-sm text-muted">
        Predictions for the next matchday. Tap &quot;Why?&quot; on any market for the reasoning, or
        &quot;Check my sportsbook odds&quot; to see if there&apos;s value in what you&apos;re being offered.
      </p>

      {fixtures.length === 0 ? (
        <p className="mt-6 text-sm text-muted">No upcoming fixtures found right now.</p>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
          {fixtures.map((f) => (
            <MatchCard
              key={`${f.date}-${f.home_team}-${f.away_team}`}
              f={f}
              homeRating={ratingsByTeam.get(f.home_team)}
              awayRating={ratingsByTeam.get(f.away_team)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
