import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CalendarDays } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useEventsCalendar } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import type { CorporateEventRow } from "@/types";

type Win = "upcoming" | "recent";

/** Event type → label + colour. */
const TYPE_META: Record<string, { label: string; color: string }> = {
  result: { label: "Results", color: "#3b82f6" },
  dividend: { label: "Dividend", color: "#10b981" },
  split: { label: "Split", color: "#8b5cf6" },
  bonus: { label: "Bonus", color: "#f59e0b" },
  rights: { label: "Rights", color: "#22d3ee" },
  buyback: { label: "Buyback", color: "#f43f5e" },
  agm: { label: "AGM", color: "#64748b" },
  fundraising: { label: "Fund Raising", color: "#ec4899" },
  board_meeting: { label: "Board Meeting", color: "#94a3b8" },
};

const FILTERS: { key: string | "all"; label: string }[] = [
  { key: "all", label: "All" },
  { key: "result", label: "Results" },
  { key: "dividend", label: "Dividend" },
  { key: "split", label: "Split" },
  { key: "bonus", label: "Bonus" },
  { key: "buyback", label: "Buyback" },
];

function meta(t: string) {
  return TYPE_META[t] ?? { label: t, color: "#94a3b8" };
}

function dayLabel(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short", year: "numeric" });
}

export default function EventsPage() {
  const [win, setWin] = useState<Win>("upcoming");
  const [type, setType] = useState<string>("all");
  const { data, isLoading } = useEventsCalendar({
    window: win,
    type: type === "all" ? undefined : type,
    days: win === "upcoming" ? 45 : 30,
    limit: 300,
  });

  const grouped = useMemo(() => {
    const by: Record<string, CorporateEventRow[]> = {};
    for (const e of data ?? []) (by[e.eventDate] ??= []).push(e);
    return Object.entries(by); // already date-ordered from the API
  }, [data]);

  return (
    <div>
      <PageHeader
        title="Events Calendar"
        description="Upcoming & recent corporate events — quarterly results, dividends, splits, bonuses, buybacks and AGMs from NSE filings."
      />

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-2">
          <Button size="sm" variant={win === "upcoming" ? "default" : "outline"} onClick={() => setWin("upcoming")}>
            Upcoming
          </Button>
          <Button size="sm" variant={win === "recent" ? "default" : "outline"} onClick={() => setWin("recent")}>
            Recent
          </Button>
        </div>
        <div className="flex flex-wrap gap-1 rounded-lg bg-muted/40 p-1">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setType(f.key)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                type === f.key ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="mt-4 space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      ) : grouped.length === 0 ? (
        <Card className="mt-4 p-6 text-sm text-muted-foreground">
          No {win} events {type !== "all" ? `of type "${meta(type).label}"` : ""} — the daily ETL keeps this current.
        </Card>
      ) : (
        <div className="mt-4 space-y-5">
          {grouped.map(([date, items]) => (
            <div key={date}>
              <div className="mb-2 flex items-center gap-2">
                <CalendarDays className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold">{dayLabel(date)}</h3>
                <span className="text-xs text-muted-foreground">· {items.length}</span>
              </div>
              <Card className="divide-y divide-border/40 overflow-hidden">
                {items.map((e, i) => {
                  const m = meta(e.eventType);
                  return (
                    <motion.div
                      key={`${e.symbol}-${e.eventType}-${i}`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center gap-3 px-3 py-2.5 hover:bg-muted/30"
                    >
                      <span
                        className="shrink-0 rounded-md px-2 py-0.5 text-[11px] font-semibold"
                        style={{ color: m.color, background: `${m.color}1a` }}
                      >
                        {m.label}
                      </span>
                      <Link to={`/stocks/${e.symbol}`} className="w-28 shrink-0 truncate font-mono text-sm font-medium hover:text-primary">
                        {e.symbol}
                      </Link>
                      <span className="min-w-0 flex-1 truncate text-xs text-muted-foreground" title={e.detail ?? ""}>
                        {e.detail || e.name}
                      </span>
                    </motion.div>
                  );
                })}
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
