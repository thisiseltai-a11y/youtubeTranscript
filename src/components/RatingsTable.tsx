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

function FormChips({ form }: { form: string[] }) {
  if (form.length === 0) {
    return <span className="text-xs text-muted">—</span>;
  }
  return (
    <div className="flex justify-end gap-1">
      {form.map((r, i) => (
        <span
          key={i}
          className={
            "flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold " +
            (r === "W"
              ? "bg-brand-soft text-brand"
              : r === "L"
                ? "text-negative"
                : "text-muted")
          }
          style={r === "L" ? { backgroundColor: "rgba(220, 38, 38, 0.12)" } : r === "D" ? { backgroundColor: "var(--border)" } : undefined}
        >
          {r}
        </span>
      ))}
    </div>
  );
}

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
      <table className="w-full min-w-[680px] text-sm">
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
            <th className="px-3 py-2.5 text-right text-xs font-semibold tracking-wide text-muted uppercase">
              Last 5
            </th>
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
              <td className="px-3 py-2.5">
                <FormChips form={r.form_last5} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
