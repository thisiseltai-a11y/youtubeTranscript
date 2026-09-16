import type { FixturePrediction, TeamRating } from "./types";

function strengthWord(netRating: number): string {
  if (netRating > 0.5) return "a strong";
  if (netRating > 0.1) return "an above-average";
  if (netRating > -0.1) return "a roughly average";
  if (netRating > -0.5) return "a below-average";
  return "a weak";
}

function thinDataNote(f: FixturePrediction): string {
  if (f.home_thin_data && f.away_thin_data) {
    return " Both teams have played fewer than 6 matches this season, so this prediction carries more uncertainty than usual.";
  }
  if (f.home_thin_data) {
    return ` ${f.home_team} have played fewer than 6 matches this season, so their rating carries more uncertainty than usual.`;
  }
  if (f.away_thin_data) {
    return ` ${f.away_team} have played fewer than 6 matches this season, so their rating carries more uncertainty than usual.`;
  }
  return "";
}

export function explainResult(f: FixturePrediction, homeRating?: TeamRating, awayRating?: TeamRating): string {
  const parts: string[] = [];
  if (homeRating && awayRating) {
    parts.push(
      `${f.home_team} rate as ${strengthWord(homeRating.net_rating)} team this season ` +
        `(net rating ${homeRating.net_rating.toFixed(2)}), and ${f.away_team} as ` +
        `${strengthWord(awayRating.net_rating)} one (${awayRating.net_rating.toFixed(2)}).`
    );
  }
  parts.push(
    `Combined with home-field advantage, that puts expected goals at ` +
      `${f.expected_home_goals.toFixed(2)} for ${f.home_team} vs ${f.expected_away_goals.toFixed(2)} for ` +
      `${f.away_team} — the win/draw/loss percentages are built directly from those.`
  );
  parts.push(thinDataNote(f));
  return parts.join(" ").trim();
}

export function explainTotalGoals(f: FixturePrediction): string {
  const total = f.expected_home_goals + f.expected_away_goals;
  const lean = total >= 2.5 ? "above" : "below";
  return (
    `Adding both teams' expected goals gives ${f.expected_home_goals.toFixed(2)} + ` +
    `${f.expected_away_goals.toFixed(2)} = ${total.toFixed(2)}, which is ${lean} the 2.5-goal line — ` +
    `that's what the Over/Under split is based on.` +
    thinDataNote(f)
  );
}

export function explainBtts(f: FixturePrediction): string {
  const bothLikely = f.expected_home_goals > 0.9 && f.expected_away_goals > 0.9;
  const base = bothLikely
    ? `Both teams project to create a reasonable scoring threat here ` +
      `(${f.expected_home_goals.toFixed(2)} and ${f.expected_away_goals.toFixed(2)} expected goals), ` +
      `which is why both teams scoring is close to a coin flip or better.`
    : `One side projects to create much less than the other ` +
      `(${f.expected_home_goals.toFixed(2)} vs ${f.expected_away_goals.toFixed(2)} expected goals), ` +
      `which lowers the chance both teams find the net.`;
  return base + thinDataNote(f);
}
