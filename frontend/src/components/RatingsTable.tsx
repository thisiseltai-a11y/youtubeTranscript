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
    <div className="overflow-x-auto rounded-xl border border-black/10 dark:border-white/10">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-black/10 bg-neutral-50 dark:border-white/10 dark:bg-white/5">
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                onClick={() => onSort(col.key)}
                className={`cursor-pointer select-none px-3 py-2 font-medium text-neutral-600 dark:text-neutral-300 ${
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
          {sorted.map((r) => (
            <tr key={r.team} className="border-b border-black/5 last:border-0 dark:border-white/5">
              <td className="px-3 py-2">
                <div className="flex items-center gap-2">
                  <span>{r.team}</span>
                  {r.thin_data && <ThinDataBadge />}
                </div>
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{r.attack.toFixed(3)}</td>
              <td className="px-3 py-2 text-right tabular-nums">{r.defense.toFixed(3)}</td>
              <td className="px-3 py-2 text-right font-medium tabular-nums">{r.net_rating.toFixed(3)}</td>
              <td className="px-3 py-2 text-right tabular-nums">{r.current_season_matches}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
