import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Layers } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDerivatives } from "@/hooks/queries";
import { formatINR, formatCompact } from "@/lib/format";
import { cn } from "@/lib/utils";

type Sort = "oi" | "pcr" | "chg_oi";

const BUILDUP: Record<string, "bull" | "bear" | "hold"> = {
  "Long buildup": "bull",
  "Short covering": "bull",
  "Short buildup": "bear",
  "Long unwinding": "bear",
};

function pcrTone(pcr: number | null): string {
  if (pcr == null) return "text-muted-foreground";
  if (pcr >= 1.3) return "text-bull";   // more puts → support/bullish
  if (pcr <= 0.7) return "text-bear";   // more calls → resistance/bearish
  return "text-muted-foreground";
}

export default function FnoPage() {
  const [sort, setSort] = useState<Sort>("oi");
  const { data, isLoading } = useDerivatives(sort);

  return (
    <div>
      <PageHeader
        title="F&O / Derivatives"
        description="Futures open interest, OI-change buildup, put/call ratio and max pain per underlying — from NSE's end-of-day F&O bhavcopy. EOD data (previous trading session)."
      />

      <div className="mt-4 flex gap-2">
        <Button size="sm" variant={sort === "oi" ? "default" : "outline"} onClick={() => setSort("oi")}>Highest OI</Button>
        <Button size="sm" variant={sort === "chg_oi" ? "default" : "outline"} onClick={() => setSort("chg_oi")}>OI change</Button>
        <Button size="sm" variant={sort === "pcr" ? "default" : "outline"} onClick={() => setSort("pcr")}>Put/Call ratio</Button>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 12 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">F&O data unavailable right now — the EOD bhavcopy refreshes after market close.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Underlying</th>
                  <th className="p-3 text-right">Futures</th>
                  <th className="p-3 text-right">OI</th>
                  <th className="p-3 text-right">OI Δ%</th>
                  <th className="p-3 text-center">Buildup</th>
                  <th className="p-3 text-right">PCR</th>
                  <th className="hidden p-3 text-right md:table-cell">Max pain</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => (
                  <motion.tr key={r.symbol} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="border-b border-border/40 hover:bg-muted/30">
                    <td className="p-3">
                      <Link to={`/stocks/${r.symbol}`} className="font-mono text-xs font-semibold hover:text-primary">{r.symbol}</Link>
                      <span className="ml-1.5 text-[10px] text-muted-foreground">{r.kind}</span>
                    </td>
                    <td className="p-3 text-right font-mono tabular">{r.futPrice != null ? formatINR(r.futPrice) : "—"}</td>
                    <td className="p-3 text-right font-mono tabular text-muted-foreground">{r.oi != null ? formatCompact(r.oi) : "—"}</td>
                    <td className={cn("p-3 text-right font-mono tabular", (r.chgOiPct ?? 0) >= 0 ? "text-bull" : "text-bear")}>
                      {r.chgOiPct != null ? `${r.chgOiPct >= 0 ? "+" : ""}${r.chgOiPct.toFixed(1)}%` : "—"}
                    </td>
                    <td className="p-3 text-center">
                      {r.buildup ? <Badge variant={BUILDUP[r.buildup] ?? "hold"}>{r.buildup}</Badge> : <span className="text-xs text-muted-foreground">—</span>}
                    </td>
                    <td className={cn("p-3 text-right font-mono tabular", pcrTone(r.pcr))}>{r.pcr != null ? r.pcr.toFixed(2) : "—"}</td>
                    <td className="hidden p-3 text-right font-mono tabular md:table-cell">{r.maxPain != null ? formatINR(r.maxPain) : "—"}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Layers className="h-3.5 w-3.5" />
        PCR &gt; 1.3 = put-heavy (often supportive); &lt; 0.7 = call-heavy. Buildup combines price and OI direction. Per-stock option chains are on each stock page.
      </p>
    </div>
  );
}
