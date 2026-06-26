import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Coins } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDividends } from "@/hooks/queries";
import { usePreferences } from "@/contexts/preferences";
import { formatINR } from "@/lib/format";

type Win = "recent" | "upcoming";

export default function DividendsPage() {
  const [win, setWin] = useState<Win>("recent");
  const { prefs } = usePreferences();
  const { data, isLoading } = useDividends(win, prefs.universe);

  return (
    <div>
      <PageHeader
        title="Dividends"
        description="Recent and upcoming dividend announcements from NSE, with the per-share amount and an indicative yield (shown where the filing states a figure)."
      />

      <div className="mt-4 flex gap-2">
        <Button size="sm" variant={win === "recent" ? "default" : "outline"} onClick={() => setWin("recent")}>Recent</Button>
        <Button size="sm" variant={win === "upcoming" ? "default" : "outline"} onClick={() => setWin("upcoming")}>Upcoming</Button>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">{Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-11 w-full" />)}</div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">No dividend announcements in this window.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Date</th>
                  <th className="p-3">Stock</th>
                  <th className="p-3 text-right">Per share</th>
                  <th className="p-3 text-right">Yield</th>
                  <th className="hidden p-3 md:table-cell">Detail</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r, i) => (
                  <motion.tr key={`${r.symbol}-${r.eventDate}-${i}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="border-b border-border/40 hover:bg-muted/30">
                    <td className="p-3 font-mono text-xs text-muted-foreground">
                      {new Date(r.eventDate).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}
                    </td>
                    <td className="p-3">
                      <Link to={`/stocks/${r.symbol}`} className="font-mono text-xs font-semibold hover:text-primary">{r.symbol}</Link>
                      <div className="max-w-[12rem] truncate text-xs text-muted-foreground">{r.name}</div>
                    </td>
                    <td className="p-3 text-right font-mono tabular">{r.amount != null ? formatINR(r.amount) : "—"}</td>
                    <td className="p-3 text-right font-mono tabular text-bull">{r.yieldPct != null ? `${r.yieldPct.toFixed(2)}%` : "—"}</td>
                    <td className="hidden max-w-[20rem] truncate p-3 text-xs text-muted-foreground md:table-cell">{r.detail}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Coins className="h-3.5 w-3.5" />
        Yield = announced dividend ÷ latest price (a single payout, not annualised). Amounts shown only where the filing specifies them.
      </p>
    </div>
  );
}
