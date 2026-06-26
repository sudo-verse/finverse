import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Crown, TrendingDown, TrendingUp } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useSuperstars } from "@/hooks/queries";
import { cn } from "@/lib/utils";

function fmtCr(v: number): string {
  if (!v) return "—";
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(1)} Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`;
  return `₹${Math.round(v).toLocaleString("en-IN")}`;
}

export default function SuperstarsPage() {
  const { data, isLoading } = useSuperstars();

  return (
    <div>
      <PageHeader
        title="Marquee Investors"
        description="Well-known investors and notable funds, tracked via their disclosed bulk & block deals on NSE — recent buys, sells and the stocks they're moving. Builds as these names transact."
      />

      {isLoading ? (
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-48 w-full rounded-xl" />)}
        </div>
      ) : !data || data.length === 0 ? (
        <Card className="mt-4">
          <CardContent className="p-8 text-center text-sm text-muted-foreground">
            No marquee-investor deals in the window yet. This fills in as tracked investors and funds make disclosed
            bulk/block trades — check back as the daily deal feed grows.
          </CardContent>
        </Card>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {data.map((s, i) => (
            <motion.div key={s.investor} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
              <Card className="glass-hover h-full">
                <CardHeader className="flex-row items-start justify-between space-y-0">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Crown className="h-4 w-4 text-primary" /> {s.investor}
                    </CardTitle>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="muted">{s.kind}</Badge>
                      <span>{s.numTrades} trade{s.numTrades === 1 ? "" : "s"}</span>
                      {s.lastActive && <span>· last {new Date(s.lastActive).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}</span>}
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="flex items-center justify-end gap-1 text-bull"><TrendingUp className="h-3 w-3" />{fmtCr(s.buyValue)}</div>
                    <div className="flex items-center justify-end gap-1 text-bear"><TrendingDown className="h-3 w-3" />{fmtCr(s.sellValue)}</div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1">
                    {s.trades.slice(0, 6).map((t, j) => (
                      <div key={j} className="flex items-center gap-2 text-xs">
                        <span className={cn("w-9 shrink-0 font-semibold", (t.side || "").toUpperCase() === "SELL" ? "text-bear" : "text-bull")}>
                          {(t.side || "").toUpperCase() === "SELL" ? "SELL" : "BUY"}
                        </span>
                        <Link to={`/stocks/${t.symbol}`} className="w-24 shrink-0 truncate font-mono font-medium hover:text-primary">
                          {t.symbol}
                        </Link>
                        <span className="flex-1 truncate text-muted-foreground">{t.name}</span>
                        <span className="shrink-0 font-mono">{fmtCr(t.value ?? 0)}</span>
                        <span className="hidden shrink-0 text-muted-foreground/70 sm:inline">
                          {new Date(t.dealDate).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <p className="mt-3 text-xs text-muted-foreground">
        Source: NSE bulk/block-deal disclosures (large trades only). Absence of a name doesn't mean inactivity — only
        disclosed deals appear.
      </p>
    </div>
  );
}
