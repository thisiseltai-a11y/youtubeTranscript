"use client";

import { useMemo, useState } from "react";
import type { TeamRating } from "@/lib/types";
import { ThinDataBadge } from "./ThinDataBadge";

type SortKey = "team" | "attack" | "defense" | "net_rating" | "current_season_matches";

const COLUMNS: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "team", label: "Team" },
  { key: "attack", label: "Attack", align: "right" },
  { key: "defense", label: "Defense", align: "right" },
  { key: "net_rating", label: "Net rating", align: "right" },
  { key: "current_season_matches", label: "Matches this season", align: "right" },
];

export function RatingsTable({ ratings }: { ratings: TeamRating[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("net_rating");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    const rows = [...ratings];
    rows.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const cmp = typeof av === "string" ? av.localeCompare(bv as string) : (av as number) - (bv as number);
      return sortDir === "asc" ? cmp : -cmp;
    });
    return rows;
  }, [ratings, sortKey, sortDir]);

  function onSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-border bg-surface shadow-sm">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-border bg-background">
            <th className="w-10 px-3 py-2.5" />
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                onClick={() => onSort(col.key)}
                className={`cursor-pointer select-none px-3 py-2.5 text-xs font-semibold tracking-wide text-muted uppercase transition-colors hover:text-foreground ${
                  col.align === "right" ? "text-right" : "text-left"
                }`}
              >
                {col.label}
                {sortKey === col.key && (sortDir === "asc" ? " ↑" : " ↓")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={r.team} className="border-b border-border transition-colors last:border-0 hover:bg-background">
              <td className="px-3 py-2.5 text-right text-xs tabular-nums text-muted">{i + 1}</td>
              <td className="px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{r.team}</span>
                  {r.thin_data && <ThinDataBadge />}
                </div>
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums text-muted">{r.attack.toFixed(3)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums text-muted">{r.defense.toFixed(3)}</td>
              <td
                className={`px-3 py-2.5 text-right font-semibold tabular-nums ${
                  r.net_rating > 0 ? "text-positive" : r.net_rating < 0 ? "text-negative" : ""
                }`}
              >
                {r.net_rating > 0 ? "+" : ""}
                {r.net_rating.toFixed(3)}
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums text-muted">{r.current_season_matches}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
