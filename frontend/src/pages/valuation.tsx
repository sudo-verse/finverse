import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Scale } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useValuationLeaderboard } from "@/hooks/queries";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

type Verdict = "undervalued" | "overvalued" | "all";

const VERDICT_BADGE: Record<string, { label: string; variant: "bull" | "bear" | "hold" }> = {
  undervalued: { label: "Undervalued", variant: "bull" },
  overvalued: { label: "Overvalued", variant: "bear" },
  "fairly valued": { label: "Fair", variant: "hold" },
};

export default function ValuationPage() {
  const [verdict, setVerdict] = useState<Verdict>("undervalued");
  const { data, isLoading } = useValuationLeaderboard(verdict === "all" ? undefined : verdict, 60);

  return (
    <div>
      <PageHeader
        title="Fair Value"
        description="Sector-relative, quality-adjusted fair value (P/E tilted by growth, P/B by ROE) versus the current price. A screening signal to surface mispricings — not a price target. Low-confidence and outlier estimates are excluded."
      />

      <div className="mt-4 flex gap-2">
        <Button size="sm" variant={verdict === "undervalued" ? "default" : "outline"} onClick={() => setVerdict("undervalued")}>
          Most undervalued
        </Button>
        <Button size="sm" variant={verdict === "overvalued" ? "default" : "outline"} onClick={() => setVerdict("overvalued")}>
          Most overvalued
        </Button>
        <Button size="sm" variant={verdict === "all" ? "default" : "outline"} onClick={() => setVerdict("all")}>
          All
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
          <p className="p-6 text-sm text-muted-foreground">No stocks match this view.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Stock</th>
                  <th className="hidden p-3 sm:table-cell">Sector</th>
                  <th className="p-3 text-right">Price</th>
                  <th className="p-3 text-right">Fair Value</th>
                  <th className="p-3 text-right">Upside</th>
                  <th className="p-3 text-center">Verdict</th>
                  <th className="hidden p-3 text-center md:table-cell">Conf.</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => {
                  const v = VERDICT_BADGE[r.verdict ?? ""] ?? VERDICT_BADGE["fairly valued"];
                  const up = r.upsidePct ?? 0;
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
                        <div className="max-w-[14rem] truncate text-xs text-muted-foreground">{r.name}</div>
                      </td>
                      <td className="hidden p-3 text-xs text-muted-foreground sm:table-cell">{r.sector ?? "—"}</td>
                      <td className="p-3 text-right font-mono tabular">{r.price != null ? formatINR(r.price) : "—"}</td>
                      <td className="p-3 text-right font-mono tabular">{r.fairValue != null ? formatINR(r.fairValue) : "—"}</td>
                      <td className="p-3 text-right">
                        <span className={cn("font-mono font-medium tabular", up >= 0 ? "text-bull" : "text-bear")}>
                          {up >= 0 ? "+" : ""}{up.toFixed(1)}%
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        <Badge variant={v.variant}>{v.label}</Badge>
                      </td>
                      <td className="hidden p-3 text-center text-xs capitalize text-muted-foreground md:table-cell">
                        {r.confidence}
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Scale className="h-3.5 w-3.5" />
        Relative model only — assumes peers are fairly priced. Cross-check with the fundamentals and scorecard on each stock page.
      </p>
    </div>
  );
}
