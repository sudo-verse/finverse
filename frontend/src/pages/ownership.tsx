import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { TrendingDown, TrendingUp } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { usePreferences } from "@/contexts/preferences";
import type { OwnershipActivityRow } from "@/types";

type Metric = "promoter" | "fii" | "dii" | "mf" | "insurance";
type Direction = "buying" | "selling";

const METRICS: { key: Metric; label: string }[] = [
  { key: "promoter", label: "Promoters" },
  { key: "fii", label: "FII / FPI" },
  { key: "dii", label: "DII" },
  { key: "mf", label: "Mutual Funds" },
  { key: "insurance", label: "Insurance" },
];

function useOwnershipActivity(metric: Metric, direction: Direction, universe: string) {
  return useQuery({
    queryKey: ["ownership-activity", metric, direction, universe],
    queryFn: async () =>
      (await apiClient.get<OwnershipActivityRow[]>("/ownership/activity", {
        params: { metric, direction, limit: 50, universe },
      })).data,
    staleTime: 10 * 60_000,
  });
}

export default function OwnershipPage() {
  const [metric, setMetric] = useState<Metric>("promoter");
  const [direction, setDirection] = useState<Direction>("buying");
  const { prefs } = usePreferences();
  const { data, isLoading } = useOwnershipActivity(metric, direction, prefs.universe);
  const label = METRICS.find((m) => m.key === metric)!.label;

  return (
    <div>
      <PageHeader
        title="Smart-Money Activity"
        description="Stocks where promoters, FIIs or DIIs increased or reduced their stake quarter-on-quarter — sourced from NSE shareholding filings."
      />

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-lg bg-muted/40 p-1">
          {METRICS.map((m) => (
            <button
              key={m.key}
              onClick={() => setMetric(m.key)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                metric === m.key ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant={direction === "buying" ? "default" : "outline"} onClick={() => setDirection("buying")}>
            <TrendingUp className="mr-1.5 h-4 w-4" /> Accumulating
          </Button>
          <Button size="sm" variant={direction === "selling" ? "default" : "outline"} onClick={() => setDirection("selling")}>
            <TrendingDown className="mr-1.5 h-4 w-4" /> Reducing
          </Button>
        </div>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            No {label} activity data yet
            {metric !== "promoter" ? " — run the shareholding ETL with --detail to populate FII/DII." : " — run the shareholding ETL to populate."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Stock</th>
                  <th className="p-3 text-right">Prev</th>
                  <th className="p-3 text-right">Latest</th>
                  <th className="p-3 text-right">Change (QoQ)</th>
                  <th className="hidden p-3 text-right sm:table-cell">Quarter</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => (
                  <motion.tr
                    key={r.symbol}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="border-b border-border/40 hover:bg-muted/30"
                  >
                    <td className="p-3">
                      <Link to={`/stocks/${r.symbol}`} className="font-mono font-medium hover:text-primary">
                        {r.symbol}
                      </Link>
                      <div className="max-w-[16rem] truncate text-xs text-muted-foreground">{r.name}</div>
                    </td>
                    <td className="p-3 text-right font-mono tabular text-muted-foreground">{r.prevPct?.toFixed(2)}%</td>
                    <td className="p-3 text-right font-mono tabular">{r.pct?.toFixed(2)}%</td>
                    <td className="p-3 text-right">
                      <span className={cn("font-mono font-medium tabular", (r.change ?? 0) >= 0 ? "text-bull" : "text-bear")}>
                        {(r.change ?? 0) >= 0 ? "+" : ""}
                        {r.change?.toFixed(2)} pp
                      </span>
                    </td>
                    <td className="hidden p-3 text-right text-xs text-muted-foreground sm:table-cell">{r.period}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
