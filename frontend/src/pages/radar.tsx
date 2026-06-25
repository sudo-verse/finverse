import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { TrendingDown, TrendingUp } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRadar } from "@/hooks/queries";
import { usePreferences } from "@/contexts/preferences";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

type Band = "high" | "low";

/** A compact bar showing where price sits in the 52-week range. */
function RangeBar({ pct, band }: { pct: number | null; band: Band }) {
  const p = Math.min(100, Math.max(0, pct ?? 0));
  return (
    <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div
        className={cn("absolute inset-y-0 left-0 rounded-full", band === "high" ? "bg-bull/40" : "bg-bear/40")}
        style={{ width: `${p}%` }}
      />
      <div
        className={cn("absolute top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full",
          band === "high" ? "bg-bull" : "bg-bear")}
        style={{ left: `${p}%` }}
      />
    </div>
  );
}

export default function RadarPage() {
  const [band, setBand] = useState<Band>("high");
  const { prefs } = usePreferences();
  const { data, isLoading } = useRadar(band, 5, prefs.universe);

  return (
    <div>
      <PageHeader
        title="52-Week Radar"
        description="Stocks pressing against their 52-week high (breakout momentum) or low (capitulation / value), closest to the extreme first."
      />

      <div className="mt-4 flex gap-2">
        <Button size="sm" variant={band === "high" ? "default" : "outline"} onClick={() => setBand("high")}>
          <TrendingUp className="mr-1.5 h-4 w-4" /> Near 52-week High
        </Button>
        <Button size="sm" variant={band === "low" ? "default" : "outline"} onClick={() => setBand("low")}>
          <TrendingDown className="mr-1.5 h-4 w-4" /> Near 52-week Low
        </Button>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">No stocks near their 52-week {band} right now.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Stock</th>
                  <th className="p-3 text-right">Price</th>
                  <th className="p-3 text-right">52w {band === "high" ? "High" : "Low"}</th>
                  <th className="p-3 text-right">{band === "high" ? "From High" : "From Low"}</th>
                  <th className="hidden p-3 md:table-cell" style={{ width: "22%" }}>Range</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => {
                  const delta = band === "high" ? r.pctFromHigh : r.pctFromLow;
                  return (
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
                      <td className="p-3 text-right font-mono tabular">{r.price != null ? formatINR(r.price) : "—"}</td>
                      <td className="p-3 text-right font-mono tabular text-muted-foreground">
                        {formatINR(band === "high" ? r.high52 ?? 0 : r.low52 ?? 0)}
                      </td>
                      <td className="p-3 text-right">
                        <span className={cn("font-mono font-medium tabular", band === "high" ? "text-bull" : "text-bear")}>
                          {Math.abs(delta ?? 0) < 0.05 ? "at " + band : `${delta?.toFixed(2)}%`}
                        </span>
                      </td>
                      <td className="hidden p-3 md:table-cell">
                        <RangeBar pct={r.pctInRange} band={band} />
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
