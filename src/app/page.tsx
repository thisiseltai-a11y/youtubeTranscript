import { FixturesSection } from "@/components/FixturesSection";
import { Header } from "@/components/Header";
import { HowItWorks } from "@/components/HowItWorks";
import { LiveScores } from "@/components/LiveScores";
import { RatingsTable } from "@/components/RatingsTable";
import { getBacktestSummary, getFixtures, getRatings } from "@/lib/api";
import type { BacktestSummary, FixturePrediction, TeamRating } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [ratings, fixtures, summary] = await Promise.all([
    getRatings().catch(() => [] as TeamRating[]),
    getFixtures().catch(() => [] as FixturePrediction[]),
    getBacktestSummary().catch(() => null as BacktestSummary | null),
  ]);

  return (
    <>
      <Header />
      <main className="flex-1">
        <LiveScores />
        <section className="mx-auto max-w-5xl px-4 pt-14 pb-16 sm:px-6">
          <span className="inline-flex items-center rounded-full bg-brand-soft px-3 py-1 text-xs font-semibold text-brand">
            Premier League · Dixon-Coles model
          </span>
          <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            Statistical EPL predictions, built on a backtested model.
          </h1>
          <p className="mt-4 max-w-2xl text-muted">
            Team ratings, match probabilities, and expected goals from a Dixon-Coles Poisson
            model — with the reasoning behind every number, and an optional check against odds
            you find elsewhere. This is analysis, not a sportsbook: it doesn&apos;t take bets or
            handle money.
          </p>
        </section>

        <HowItWorks summary={summary} />
        <FixturesSection fixtures={fixtures} ratings={ratings} />

        <section id="ratings" className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
          <h2 className="text-xl font-semibold tracking-tight">Team ratings</h2>
          <p className="mt-1 text-sm text-muted">
            Attack/defense ratings on a log scale (0 = league average). Sort any column.
          </p>
          <div className="mt-6">
            <RatingsTable ratings={ratings} />
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-8 text-center text-xs text-muted">
        Statistical model output only. Not financial or betting advice. 18+.
      </footer>
    </>
  );
}
