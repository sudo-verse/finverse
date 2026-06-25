import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useStockEarnings } from "@/hooks/queries";
import type { EarningsMomentum } from "@/types";
import { formatFraction, formatINRCompact } from "@/lib/format";
import { cn } from "@/lib/utils";

const MOMENTUM: Record<string, { label: string; variant: "bull" | "bear" | "hold" }> = {
  accelerating: { label: "PAT growth accelerating", variant: "bull" },
  decelerating: { label: "PAT growth decelerating", variant: "bear" },
  steady: { label: "PAT growth steady", variant: "hold" },
};

function frac(v: number | null) {
  return (
    <span className={cn("font-mono tabular", v == null ? "text-muted-foreground" : v >= 0 ? "text-bull" : "text-bear")}>
      {formatFraction(v)}
    </span>
  );
}

function MomentumBadge({ momentum }: { momentum: EarningsMomentum }) {
  if (!momentum || !MOMENTUM[momentum]) return null;
  const m = MOMENTUM[momentum];
  return <Badge variant={m.variant} className="font-normal">{m.label}</Badge>;
}

export function EarningsPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useStockEarnings(symbol);
  const years = data?.years ?? [];

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-primary" /> Earnings Growth
        </CardTitle>
        <MomentumBadge momentum={data?.momentum ?? null} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-48 w-full rounded-lg" />
        ) : years.length < 2 ? (
          <p className="text-sm text-muted-foreground">No annual earnings history available for {symbol}.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-2.5">FY</th>
                  <th className="p-2.5 text-right">Revenue</th>
                  <th className="p-2.5 text-right">Rev YoY</th>
                  <th className="p-2.5 text-right">PAT</th>
                  <th className="p-2.5 text-right">PAT YoY</th>
                  <th className="hidden p-2.5 text-right sm:table-cell">Net Margin</th>
                </tr>
              </thead>
              <tbody>
                {years.map((y) => (
                  <tr key={y.fy} className="border-b border-border/40 hover:bg-muted/30">
                    <td className="p-2.5 font-mono font-medium">{y.fy}</td>
                    <td className="p-2.5 text-right font-mono tabular">
                      {y.revenue != null ? formatINRCompact(y.revenue) : "—"}
                    </td>
                    <td className="p-2.5 text-right">{frac(y.revenueYoy)}</td>
                    <td className="p-2.5 text-right font-mono tabular">
                      {y.netIncome != null ? formatINRCompact(y.netIncome) : "—"}
                    </td>
                    <td className="p-2.5 text-right">{frac(y.patYoy)}</td>
                    <td className="hidden p-2.5 text-right font-mono tabular text-muted-foreground sm:table-cell">
                      {y.netMargin != null ? `${(y.netMargin * 100).toFixed(1)}%` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
