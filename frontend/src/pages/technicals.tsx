import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTechnicalScreen } from "@/hooks/queries";
import { usePreferences } from "@/contexts/preferences";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

type Signal = "bullish" | "bearish";

const TREND: Record<string, "bull" | "bear" | "hold"> = {
  bullish: "bull",
  bearish: "bear",
  neutral: "hold",
};

function rsiTone(rsi: number | null): string {
  if (rsi == null) return "text-muted-foreground";
  if (rsi >= 70) return "text-bear";
  if (rsi <= 30) return "text-bull";
  return rsi >= 50 ? "text-bull" : "text-muted-foreground";
}

export default function TechnicalsPage() {
  const [signal, setSignal] = useState<Signal>("bullish");
  const { prefs } = usePreferences();
  const { data, isLoading } = useTechnicalScreen(signal, 60, prefs.universe);

  return (
    <div>
      <PageHeader
        title="Technical Screener"
        description="Stocks ranked by a composite technical score — price versus 20/50-day moving averages, RSI, MACD and position in the 52-week range. Computed from our own daily price history. A trading-signal view, not advice."
      />

      <div className="mt-4 flex gap-2">
        <Button size="sm" variant={signal === "bullish" ? "default" : "outline"} onClick={() => setSignal("bullish")}>
          Strongest setups
        </Button>
        <Button size="sm" variant={signal === "bearish" ? "default" : "outline"} onClick={() => setSignal("bearish")}>
          Weakest setups
        </Button>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-11 w-full" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            No stocks with enough price history to screen in this universe yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Stock</th>
                  <th className="hidden p-3 sm:table-cell">Sector</th>
                  <th className="p-3 text-right">Price</th>
                  <th className="p-3 text-right">Score</th>
                  <th className="p-3 text-center">Trend</th>
                  <th className="p-3 text-right">RSI</th>
                  <th className="hidden p-3 text-center md:table-cell">MACD</th>
                  <th className="hidden p-3 text-center lg:table-cell">vs 50-DMA</th>
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
                    <td className="hidden p-3 text-xs text-muted-foreground sm:table-cell">{r.sector ?? "—"}</td>
                    <td className="p-3 text-right font-mono tabular">{r.price != null ? formatINR(r.price) : "—"}</td>
                    <td className="p-3 text-right font-mono font-medium tabular">{Math.round(r.score)}</td>
                    <td className="p-3 text-center">
                      <Badge variant={TREND[r.trend] ?? "hold"}>{r.trend}</Badge>
                    </td>
                    <td className={cn("p-3 text-right font-mono tabular", rsiTone(r.rsi))}>
                      {r.rsi != null ? r.rsi.toFixed(0) : "—"}
                    </td>
                    <td className="hidden p-3 text-center md:table-cell">
                      <span className={cn("font-mono text-xs", (r.macdHist ?? 0) >= 0 ? "text-bull" : "text-bear")}>
                        {(r.macdHist ?? 0) >= 0 ? "bullish" : "bearish"}
                      </span>
                    </td>
                    <td className="hidden p-3 text-center lg:table-cell">
                      {r.aboveSma50 == null ? (
                        <span className="text-xs text-muted-foreground">—</span>
                      ) : (
                        <span className={cn("text-xs font-medium", r.aboveSma50 ? "text-bull" : "text-bear")}>
                          {r.aboveSma50 ? "above" : "below"}
                        </span>
                      )}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Activity className="h-3.5 w-3.5" />
        Score blends price vs 20/50-DMA, RSI and MACD with 52-week position. Full indicators (incl. 200-DMA, pivots) are
        on each stock page. Accuracy scales with price-history depth.
      </p>
    </div>
  );
}
