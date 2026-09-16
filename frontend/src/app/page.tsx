import { BetEvaluator } from "@/components/BetEvaluator";
import { FixturesSection } from "@/components/FixturesSection";
import { Header } from "@/components/Header";
import { HowItWorks } from "@/components/HowItWorks";
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
        <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Statistical EPL predictions, built on a backtested model.
          </h1>
          <p className="mt-4 max-w-2xl text-neutral-600 dark:text-neutral-300">
            Team ratings, match probabilities, and expected goals from a Dixon-Coles Poisson
            model — plus a bet evaluator to compare it against odds you find elsewhere. This is
            analysis, not a sportsbook: it doesn&apos;t take bets or handle money.
          </p>
        </section>

        <HowItWorks summary={summary} />
        <FixturesSection fixtures={fixtures} />

        <section id="ratings" className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
          <h2 className="text-xl font-semibold">Team ratings</h2>
          <p className="mt-1 text-sm text-neutral-500">
            Attack/defense ratings on a log scale (0 = league average). Sort any column.
          </p>
          <div className="mt-6">
            <RatingsTable ratings={ratings} />
          </div>
        </section>

        <BetEvaluator fixtures={fixtures} />
      </main>

      <footer className="border-t border-black/10 py-8 text-center text-xs text-neutral-500 dark:border-white/10">
        Statistical model output only. Not financial or betting advice. 18+.
      </footer>
    </>
  );
}
