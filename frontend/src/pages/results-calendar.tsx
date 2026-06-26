import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CalendarClock } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useResultsCalendar } from "@/hooks/queries";
import { usePreferences } from "@/contexts/preferences";
import { cn } from "@/lib/utils";

type Win = "upcoming" | "recent";

const TAG: Record<string, "bull" | "bear" | "hold"> = {
  Strong: "bull",
  Positive: "bull",
  Soft: "hold",
  Weak: "bear",
};

function pct(v: number | null): string {
  return v == null ? "—" : `${v >= 0 ? "+" : ""}${(v * 100).toFixed(0)}%`;
}

export default function ResultsCalendarPage() {
  const [win, setWin] = useState<Win>("upcoming");
  const { prefs } = usePreferences();
  const { data, isLoading } = useResultsCalendar(win, prefs.universe);

  return (
    <div>
      <PageHeader
        title="Results Calendar"
        description="Upcoming and recent earnings-announcement dates from NSE, each tagged with the company's latest annual PAT/revenue trend and momentum. (No analyst estimates available, so this is a fundamental-trend tag, not a vs-estimate beat/miss.)"
      />

      <div className="mt-4 flex gap-2">
        <Button size="sm" variant={win === "upcoming" ? "default" : "outline"} onClick={() => setWin("upcoming")}>
          Upcoming
        </Button>
        <Button size="sm" variant={win === "recent" ? "default" : "outline"} onClick={() => setWin("recent")}>
          Recently reported
        </Button>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-11 w-full" />)}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            {win === "upcoming" ? "No result dates announced in this window." : "No recently-reported results in this window."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Date</th>
                  <th className="p-3">Stock</th>
                  <th className="p-3 text-right">PAT YoY</th>
                  <th className="hidden p-3 text-right sm:table-cell">Rev YoY</th>
                  <th className="hidden p-3 text-center md:table-cell">Momentum</th>
                  <th className="p-3 text-center">Trend</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r, i) => (
                  <motion.tr
                    key={`${r.symbol}-${r.eventDate}-${i}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="border-b border-border/40 hover:bg-muted/30"
                  >
                    <td className="p-3 font-mono text-xs text-muted-foreground">
                      {new Date(r.eventDate).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}
                    </td>
                    <td className="p-3">
                      <Link to={`/stocks/${r.symbol}`} className="font-mono text-xs font-semibold hover:text-primary">
                        {r.symbol}
                      </Link>
                      <div className="max-w-[14rem] truncate text-xs text-muted-foreground">{r.name}</div>
                    </td>
                    <td className={cn("p-3 text-right font-mono tabular", (r.patYoy ?? 0) >= 0 ? "text-bull" : "text-bear")}>
                      {pct(r.patYoy)}
                    </td>
                    <td className="hidden p-3 text-right font-mono tabular sm:table-cell">{pct(r.revenueYoy)}</td>
                    <td className="hidden p-3 text-center text-xs capitalize text-muted-foreground md:table-cell">
                      {r.momentum ?? "—"}
                    </td>
                    <td className="p-3 text-center">
                      {r.tag ? <Badge variant={TAG[r.tag] ?? "hold"}>{r.tag}</Badge> : <span className="text-xs text-muted-foreground">—</span>}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <CalendarClock className="h-3.5 w-3.5" />
        Trend tags reflect the latest full-year PAT growth + momentum, not the just-reported quarter. Dates sourced from NSE.
      </p>
    </div>
  );
}
