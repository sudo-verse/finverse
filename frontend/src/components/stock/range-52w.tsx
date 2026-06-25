import { useQuery } from "@tanstack/react-query";
import { getStockRange } from "@/api/services";
import { Badge } from "@/components/ui/badge";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Slim 52-week range bar — shown inline on the stock page header area. */
export function Range52w({ symbol }: { symbol: string }) {
  const { data } = useQuery({
    queryKey: ["range-52w", symbol],
    queryFn: () => getStockRange(symbol),
    staleTime: 10 * 60_000,
  });

  if (!data || data.high52 == null || data.low52 == null || data.pctInRange == null) return null;
  const p = Math.min(100, Math.max(0, data.pctInRange));

  return (
    <div className="rounded-xl border border-border/60 bg-card/40 p-3">
      <div className="mb-1.5 flex items-center justify-between text-xs">
        <span className="font-medium text-muted-foreground">52-Week Range</span>
        {data.atHigh && <Badge variant="bull">At 52w high</Badge>}
        {data.atLow && <Badge variant="bear">At 52w low</Badge>}
      </div>
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-gradient-to-r from-bear/30 via-muted to-bull/30">
        <div
          className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary shadow ring-2 ring-background"
          style={{ left: `${p}%` }}
        />
      </div>
      <div className="mt-1.5 flex items-center justify-between font-mono text-xs tabular">
        <span className="text-bear">{formatINR(data.low52)}</span>
        <span className={cn("text-muted-foreground")}>
          {data.pctFromHigh != null ? `${data.pctFromHigh.toFixed(1)}% from high` : ""}
        </span>
        <span className="text-bull">{formatINR(data.high52)}</span>
      </div>
    </div>
  );
}
