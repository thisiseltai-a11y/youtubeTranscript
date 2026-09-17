import type { FixturePrediction, TeamRating } from "./types";

export interface Fact {
  label: string;
  value: string;
}

export interface Explanation {
  facts: Fact[];
  note?: string;
}

function strengthWord(netRating: number): string {
  if (netRating > 0.5) return "Strong";
  if (netRating > 0.1) return "Above average";
  if (netRating > -0.1) return "Roughly average";
  if (netRating > -0.5) return "Below average";
  return "Weak";
}

function thinDataNote(f: FixturePrediction): string | undefined {
  if (f.home_thin_data && f.away_thin_data) {
    return "Both teams have played fewer than 6 matches this season, so this carries more uncertainty than usual.";
  }
  if (f.home_thin_data) {
    return `${f.home_team} have played fewer than 6 matches this season, so their rating carries more uncertainty than usual.`;
  }
  if (f.away_thin_data) {
    return `${f.away_team} have played fewer than 6 matches this season, so their rating carries more uncertainty than usual.`;
  }
  return undefined;
}

export function explainResult(f: FixturePrediction, homeRating?: TeamRating, awayRating?: TeamRating): Explanation {
  const facts: Fact[] = [];
  if (homeRating) {
    facts.push({ label: `${f.home_team} form`, value: `${strengthWord(homeRating.net_rating)} (${homeRating.net_rating >= 0 ? "+" : ""}${homeRating.net_rating.toFixed(2)})` });
  }
  if (awayRating) {
    facts.push({ label: `${f.away_team} form`, value: `${strengthWord(awayRating.net_rating)} (${awayRating.net_rating >= 0 ? "+" : ""}${awayRating.net_rating.toFixed(2)})` });
  }
  facts.push({
    label: "Expected goals",
    value: `${f.expected_home_goals.toFixed(2)} – ${f.expected_away_goals.toFixed(2)}`,
  });
  facts.push({ label: "Includes", value: "Home-field advantage" });
  return { facts, note: thinDataNote(f) };
}

export function explainTotalGoals(f: FixturePrediction): Explanation {
  const total = f.expected_home_goals + f.expected_away_goals;
  return {
    facts: [
      { label: `${f.home_team} expected goals`, value: f.expected_home_goals.toFixed(2) },
      { label: `${f.away_team} expected goals`, value: f.expected_away_goals.toFixed(2) },
      { label: "Combined total", value: `${total.toFixed(2)} (line is 2.5)` },
    ],
    note: thinDataNote(f),
  };
}

export function explainBtts(f: FixturePrediction): Explanation {
  const bothLikely = f.expected_home_goals > 0.9 && f.expected_away_goals > 0.9;
  return {
    facts: [
      { label: `${f.home_team} expected goals`, value: f.expected_home_goals.toFixed(2) },
      { label: `${f.away_team} expected goals`, value: f.expected_away_goals.toFixed(2) },
      {
        label: "Reading",
        value: bothLikely ? "Both sides project to threaten" : "One side projects much weaker",
      },
    ],
    note: thinDataNote(f),
  };
}
