import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Rocket } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useIpos } from "@/hooks/queries";
import { cn } from "@/lib/utils";

type Status = "open" | "upcoming" | "listed";

const TABS: { key: Status; label: string }[] = [
  { key: "open", label: "Open now" },
  { key: "upcoming", label: "Upcoming" },
  { key: "listed", label: "Recently listed" },
];

/** Subscription multiple → colour (oversubscribed = bullish demand). */
function subTone(x: number): string {
  if (x >= 10) return "text-bull";
  if (x >= 1) return "text-emerald-400";
  return "text-muted-foreground";
}

export default function IposPage() {
  const [status, setStatus] = useState<Status>("open");
  const { data, isLoading } = useIpos(status);

  return (
    <div>
      <PageHeader
        title="IPO Tracker"
        description="Mainboard & SME public issues from NSE — open now (with live subscription), upcoming, and recently listed. Refreshed every ~30 minutes."
      />

      <div className="mt-4 flex gap-2">
        {TABS.map((t) => (
          <Button key={t.key} size="sm" variant={status === t.key ? "default" : "outline"} onClick={() => setStatus(t.key)}>
            {t.label}
          </Button>
        ))}
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            {status === "open" ? "No IPOs open right now." : status === "upcoming" ? "No upcoming IPOs announced." : "No recent listings."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Company</th>
                  <th className="p-3">Price band</th>
                  <th className="hidden p-3 sm:table-cell">{status === "listed" ? "Listed" : "Open → Close"}</th>
                  {status === "open" && <th className="p-3 text-right">Subscription</th>}
                  <th className="p-3 text-center">Type</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r, i) => (
                  <motion.tr
                    key={`${r.symbol}-${r.name}-${i}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="border-b border-border/40 hover:bg-muted/30"
                  >
                    <td className="p-3">
                      {r.symbol ? (
                        <Link to={`/stocks/${r.symbol}`} className="font-mono text-xs font-semibold hover:text-primary">
                          {r.symbol}
                        </Link>
                      ) : (
                        <span className="font-mono text-xs">—</span>
                      )}
                      <div className="max-w-[16rem] truncate text-xs text-muted-foreground">{r.name}</div>
                    </td>
                    <td className="p-3 font-mono text-xs">{r.priceBand ?? "—"}</td>
                    <td className="hidden p-3 text-xs text-muted-foreground sm:table-cell">
                      {status === "listed" ? (r.listingDate ?? "—") : `${r.openDate ?? "—"} → ${r.closeDate ?? "—"}`}
                    </td>
                    {status === "open" && (
                      <td className="p-3 text-right font-mono text-xs">
                        {r.subscription != null ? (
                          <span className={cn("font-semibold", subTone(r.subscription))}>{r.subscription.toFixed(2)}×</span>
                        ) : "—"}
                      </td>
                    )}
                    <td className="p-3 text-center">
                      <Badge variant={r.category === "SME" ? "hold" : "muted"}>{r.category ?? "—"}</Badge>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Rocket className="h-3.5 w-3.5" />
        Subscription is the live demand multiple (×). SME issues carry higher risk and lower liquidity. Sourced from NSE.
      </p>
    </div>
  );
}
