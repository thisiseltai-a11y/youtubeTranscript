"use client";

import { useEffect, useState } from "react";
import { getLiveScores } from "@/lib/api";
import type { LiveScore } from "@/lib/types";

const POLL_MS = 30_000;

function fmtKickoff(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function ScoreRow({ s }: { s: LiveScore }) {
  const isLive = s.status_short !== "NS" && s.status_short !== "FT" && s.status_short !== "AET" && s.status_short !== "PEN";
  const notStarted = s.status_short === "NS";

  return (
    <div className="flex items-center justify-between gap-3 rounded-xl bg-background px-3 py-2.5">
      <div className="min-w-0 flex-1 truncate text-sm font-medium">{s.home_team}</div>
      <div className="shrink-0 text-center">
        {notStarted ? (
          <div className="text-xs text-muted">{fmtKickoff(s.kickoff)}</div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold tabular-nums">
              {s.home_goals ?? 0} – {s.away_goals ?? 0}
            </span>
            <span
              className={
                isLive
                  ? "rounded-full bg-brand-soft px-1.5 py-0.5 text-[10px] font-semibold text-brand"
                  : "text-[10px] font-medium text-muted"
              }
            >
              {s.status_label}
            </span>
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1 truncate text-right text-sm font-medium">{s.away_team}</div>
    </div>
  );
}

export function LiveScores() {
  const [scores, setScores] = useState<LiveScore[] | null>(null);

  useEffect(() => {
    let cancelled = false;

    function load() {
      getLiveScores()
        .then((s) => {
          if (!cancelled) setScores(s);
        })
        .catch(() => {
          if (!cancelled) setScores((prev) => prev ?? []);
        });
    }

    load();
    const interval = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (scores === null || scores.length === 0) {
    return null;
  }

  return (
    <section className="mx-auto max-w-5xl px-4 pt-6 sm:px-6">
      <div className="rounded-2xl border border-brand/20 bg-surface p-4 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-brand" />
          </span>
          <h2 className="text-sm font-semibold tracking-tight">Today&apos;s EPL scores</h2>
        </div>
        <div className="space-y-2">
          {scores.map((s) => (
            <ScoreRow key={s.fixture_id ?? `${s.home_team}-${s.away_team}`} s={s} />
          ))}
        </div>
      </div>
    </section>
  );
}
