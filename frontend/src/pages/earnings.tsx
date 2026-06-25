import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { TrendingDown, TrendingUp } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useEarningsTracker } from "@/hooks/queries";
import { usePreferences } from "@/contexts/preferences";
import type { EarningsMomentum } from "@/types";
import { formatFraction, formatINRCompact } from "@/lib/format";
import { cn } from "@/lib/utils";

type Sort = "pat" | "revenue" | "margin";

const SORTS: { key: Sort; label: string }[] = [
  { key: "pat", label: "PAT Growth" },
  { key: "revenue", label: "Revenue Growth" },
  { key: "margin", label: "Margin Expansion" },
];

const MOMENTUM: Record<string, { label: string; variant: "bull" | "bear" | "hold" }> = {
  accelerating: { label: "Accelerating", variant: "bull" },
  decelerating: { label: "Decelerating", variant: "bear" },
  steady: { label: "Steady", variant: "hold" },
};

/** A tiny inline sparkline for a trailing earnings series. */
function Sparkline({ values, up }: { values: number[]; up: boolean }) {
  if (values.length < 2) return <span className="text-xs text-muted-foreground">—</span>;
  const w = 84;
  const h = 24;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / span) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} className="overflow-visible">
      <polyline
        points={pts}
        fill="none"
        strokeWidth={1.5}
        className={up ? "stroke-bull" : "stroke-bear"}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

/** Signed growth fraction with red/green colouring. */
function Growth({ value, digits = 1 }: { value: number | null; digits?: number }) {
  if (value === null || value === undefined) return <span className="text-muted-foreground">—</span>;
  return (
    <span className={cn("font-mono font-medium tabular", value >= 0 ? "text-bull" : "text-bear")}>
      {formatFraction(value, digits)}
    </span>
  );
}

function MomentumBadge({ momentum }: { momentum: EarningsMomentum }) {
  if (!momentum || !MOMENTUM[momentum]) return <span className="text-muted-foreground">—</span>;
  const m = MOMENTUM[momentum];
  return <Badge variant={m.variant}>{m.label}</Badge>;
}

export default function EarningsPage() {
  const [sort, setSort] = useState<Sort>("pat");
  const { prefs } = usePreferences();
  const { data, isLoading } = useEarningsTracker(sort, 50, prefs.universe);

  return (
    <div>
      <PageHeader
        title="Earnings Momentum"
        description="Latest-FY year-over-year growth across the universe. With no analyst estimates, momentum reflects whether PAT growth is accelerating or decelerating versus the prior year — not a beat/miss vs. consensus."
      />

      <div className="mt-4 flex flex-wrap gap-2">
        {SORTS.map((s) => (
          <Button
            key={s.key}
            size="sm"
            variant={sort === s.key ? "default" : "outline"}
            onClick={() => setSort(s.key)}
          >
            {s.key === "margin" ? null : sort === s.key ? (
              <TrendingUp className="mr-1.5 h-4 w-4" />
            ) : (
              <TrendingDown className="mr-1.5 h-4 w-4 opacity-40" />
            )}
            {s.label}
          </Button>
        ))}
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-11 w-full" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">No earnings data available yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Stock</th>
                  <th className="p-3 text-center">FY</th>
                  <th className="p-3 text-right">Revenue</th>
                  <th className="p-3 text-right">Rev YoY</th>
                  <th className="p-3 text-right">PAT</th>
                  <th className="p-3 text-right">PAT YoY</th>
                  <th className="hidden p-3 text-right md:table-cell">Margin Δ</th>
                  <th className="p-3 text-center">Momentum</th>
                  <th className="hidden p-3 lg:table-cell">Trend</th>
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
                      <div className="max-w-[14rem] truncate text-xs text-muted-foreground">{r.name}</div>
                    </td>
                    <td className="p-3 text-center font-mono text-xs text-muted-foreground">{r.fy}</td>
                    <td className="p-3 text-right font-mono tabular">
                      {r.revenue != null ? formatINRCompact(r.revenue) : "—"}
                    </td>
                    <td className="p-3 text-right">
                      <Growth value={r.revenueYoy} />
                    </td>
                    <td className="p-3 text-right font-mono tabular">
                      {r.netIncome != null ? formatINRCompact(r.netIncome) : "—"}
                    </td>
                    <td className="p-3 text-right">
                      <Growth value={r.patYoy} />
                    </td>
                    <td className="hidden p-3 text-right md:table-cell">
                      {r.marginDelta != null ? (
                        <span className={cn("font-mono tabular", r.marginDelta >= 0 ? "text-bull" : "text-bear")}>
                          {r.marginDelta >= 0 ? "+" : ""}
                          {r.marginDelta.toFixed(1)}pp
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="p-3 text-center">
                      <MomentumBadge momentum={r.momentum} />
                    </td>
                    <td className="hidden p-3 lg:table-cell">
                      <Sparkline values={r.trend} up={(r.patYoy ?? 0) >= 0} />
                    </td>
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
