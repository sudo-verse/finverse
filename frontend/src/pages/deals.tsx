import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeftRight } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDeals } from "@/hooks/queries";
import { cn } from "@/lib/utils";

type DealType = "all" | "bulk" | "block";
type Side = "all" | "BUY" | "SELL";

/** ₹ value → compact crore/lakh, e.g. ₹2.1 Cr / ₹80.0 L. */
function fmtValue(v: number | null): string {
  if (v == null) return "—";
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(1)} Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`;
  return `₹${Math.round(v).toLocaleString("en-IN")}`;
}

function fmtQty(q: number | null): string {
  if (q == null) return "—";
  if (q >= 1e7) return `${(q / 1e7).toFixed(2)} Cr`;
  if (q >= 1e5) return `${(q / 1e5).toFixed(2)} L`;
  return q.toLocaleString("en-IN");
}

export default function DealsPage() {
  const [type, setType] = useState<DealType>("all");
  const [side, setSide] = useState<Side>("all");
  const { data, isLoading } = useDeals({
    type: type === "all" ? undefined : type,
    side: side === "all" ? undefined : side,
    days: 30,
    limit: 200,
  });

  return (
    <div>
      <PageHeader
        title="Bulk & Block Deals"
        description="Large disclosed trades by named clients (often funds & big investors) — sourced from NSE's daily large-deal snapshot, biggest by value first."
      />

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-lg bg-muted/40 p-1">
          {(["all", "bulk", "block"] as DealType[]).map((t) => (
            <button
              key={t}
              onClick={() => setType(t)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors",
                type === t ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {t === "all" ? "All deals" : t}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant={side === "all" ? "default" : "outline"} onClick={() => setSide("all")}>
            Both
          </Button>
          <Button size="sm" variant={side === "BUY" ? "default" : "outline"} onClick={() => setSide("BUY")}>
            Buys
          </Button>
          <Button size="sm" variant={side === "SELL" ? "default" : "outline"} onClick={() => setSide("SELL")}>
            Sells
          </Button>
        </div>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            No deals yet — the daily ETL populates this after market close.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Stock</th>
                  <th className="p-3">Client</th>
                  <th className="p-3 text-center">Side</th>
                  <th className="p-3 text-right">Qty</th>
                  <th className="p-3 text-right">Price</th>
                  <th className="p-3 text-right">Value</th>
                  <th className="hidden p-3 text-center sm:table-cell">Type</th>
                  <th className="hidden p-3 text-right md:table-cell">Date</th>
                </tr>
              </thead>
              <tbody>
                {data.map((d, i) => (
                  <motion.tr
                    key={`${d.symbol}-${d.clientName}-${d.quantity}-${i}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="border-b border-border/40 hover:bg-muted/30"
                  >
                    <td className="p-3">
                      <Link to={`/stocks/${d.symbol}`} className="font-mono font-medium hover:text-primary">
                        {d.symbol}
                      </Link>
                      <div className="max-w-[12rem] truncate text-xs text-muted-foreground">{d.name}</div>
                    </td>
                    <td className="p-3">
                      <span className="block max-w-[18rem] truncate text-xs">{d.clientName}</span>
                    </td>
                    <td className="p-3 text-center">
                      <Badge variant={d.side === "BUY" ? "bull" : "bear"}>{d.side}</Badge>
                    </td>
                    <td className="p-3 text-right font-mono tabular text-muted-foreground">{fmtQty(d.quantity)}</td>
                    <td className="p-3 text-right font-mono tabular">{d.price != null ? `₹${d.price}` : "—"}</td>
                    <td className="p-3 text-right font-mono font-medium tabular">{fmtValue(d.value)}</td>
                    <td className="hidden p-3 text-center sm:table-cell">
                      <span className="text-xs capitalize text-muted-foreground">{d.dealType}</span>
                    </td>
                    <td className="hidden p-3 text-right text-xs text-muted-foreground md:table-cell">
                      {new Date(d.dealDate).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <ArrowLeftRight className="h-3.5 w-3.5" />
        Bulk deals = ≥0.5% of shares in a session; block deals = negotiated single trades. History builds daily.
      </p>
    </div>
  );
}
