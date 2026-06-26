import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowDown, ArrowUp, Gauge, Minus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useConvictionLeaderboard } from "@/hooks/queries";
import { usePreferences } from "@/contexts/preferences";
import { cn } from "@/lib/utils";
import type { ConvictionPillar } from "@/types";

type Order = "top" | "bottom";

function scoreTone(score: number): string {
  if (score >= 68) return "text-bull";
  if (score >= 56) return "text-emerald-400";
  if (score >= 44) return "text-muted-foreground";
  return "text-bear";
}
function scoreBarCls(score: number): string {
  if (score >= 68) return "bg-bull";
  if (score >= 56) return "bg-emerald-400";
  if (score >= 44) return "bg-slate-400";
  return "bg-bear";
}

const VERDICT_LABEL: Record<string, string> = {
  "high conviction": "High conviction",
  constructive: "Constructive",
  neutral: "Neutral",
  weak: "Weak",
};

function PillarChip({ p }: { p: ConvictionPillar }) {
  const Icon = p.signal === "up" ? ArrowUp : p.signal === "down" ? ArrowDown : Minus;
  return (
    <span
      title={p.detail ?? undefined}
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium",
        p.signal === "up" && "border-bull/25 bg-bull/10 text-bull",
        p.signal === "down" && "border-bear/25 bg-bear/10 text-bear",
        (p.signal === "neutral" || p.signal === "na") && "border-border/60 bg-muted/40 text-muted-foreground",
      )}
    >
      <Icon className="h-2.5 w-2.5" />
      {p.label}
    </span>
  );
}

export default function SentimentPage() {
  const [order, setOrder] = useState<Order>("top");
  const { prefs } = usePreferences();
  const navigate = useNavigate();
  const { data, isLoading } = useConvictionLeaderboard(order, 60, prefs.universe);

  return (
    <div>
      <PageHeader
        title="Sentiment Intelligence"
        description="One composite read per stock — valuation, earnings momentum, smart money, insider/SAST, 52-week trend and news & mood, fused into a single 0–100 score. Click any stock for the full breakdown. A screening synthesis, not advice."
      />

      <div className="mt-4 flex gap-2">
        <Button size="sm" variant={order === "top" ? "default" : "outline"} onClick={() => setOrder("top")}>
          Strongest
        </Button>
        <Button size="sm" variant={order === "bottom" ? "default" : "outline"} onClick={() => setOrder("bottom")}>
          Weakest (avoid)
        </Button>
      </div>

      <Card className="mt-4 divide-y divide-border/40">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 12 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            No stocks have enough signal coverage to score in this universe yet.
          </p>
        ) : (
          data.map((r, i) => (
            <motion.div
              key={r.symbol}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onClick={() => navigate(`/sentiment/${r.symbol}`)}
              className="flex cursor-pointer items-center gap-4 p-3.5 hover:bg-muted/20"
            >
              <span className="w-5 shrink-0 text-right font-mono text-xs text-muted-foreground/60">{i + 1}</span>

              <div className="min-w-0 flex-1">
                <div className="flex items-baseline gap-2">
                  <span className="font-mono text-sm font-semibold">{r.symbol}</span>
                  <span className="truncate text-xs text-muted-foreground">{r.name}</span>
                </div>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {r.pillars.slice(0, 6).map((p) => <PillarChip key={p.key} p={p} />)}
                </div>
              </div>

              <div className="w-32 shrink-0 sm:w-40">
                <div className="flex items-baseline justify-between">
                  <span className={cn("font-mono text-lg font-bold tabular", scoreTone(r.score))}>
                    {Math.round(r.score)}
                  </span>
                  <span className="hidden text-[10px] uppercase tracking-wide text-muted-foreground sm:inline">
                    {VERDICT_LABEL[r.verdict] ?? r.verdict}
                  </span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted/50">
                  <div className={cn("h-full rounded-full", scoreBarCls(r.score))} style={{ width: `${r.score}%` }} />
                </div>
              </div>
            </motion.div>
          ))
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Gauge className="h-3.5 w-3.5" />
        A weighted blend of the available pillars (renormalised when some are missing); a stock needs at least three to
        be ranked. Tap a stock to open its full intelligence breakdown.
      </p>
    </div>
  );
}
