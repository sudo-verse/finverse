import { Layers } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useOptionChain } from "@/hooks/queries";
import { formatINR, formatCompact } from "@/lib/format";
import { cn } from "@/lib/utils";

export function OptionChainPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useOptionChain(symbol);

  if (isLoading) {
    return (
      <Card className="mt-6">
        <CardHeader><CardTitle>Option Chain</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-40 w-full rounded-lg" /></CardContent>
      </Card>
    );
  }
  if (!data || data.strikes.length === 0) return null;

  const maxOi = Math.max(...data.strikes.flatMap((s) => [s.ceOi, s.peOi]), 1);

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-primary" /> Option Chain
        </CardTitle>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {data.expiry && <span>Exp {data.expiry}</span>}
          {data.pcr != null && <span>PCR <span className="font-mono font-medium text-foreground">{data.pcr.toFixed(2)}</span></span>}
          {data.maxPain != null && <span>Max pain <span className="font-mono font-medium text-foreground">{formatINR(data.maxPain)}</span></span>}
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-muted-foreground">
                <th className="p-1.5 text-left font-medium">Call OI</th>
                <th className="p-1.5 text-center font-medium">Strike</th>
                <th className="p-1.5 text-right font-medium">Put OI</th>
              </tr>
            </thead>
            <tbody>
              {data.strikes.map((s) => {
                const atm = data.underlying != null && Math.abs(s.strike - data.underlying) ===
                  Math.min(...data.strikes.map((x) => Math.abs(x.strike - (data.underlying ?? 0))));
                return (
                  <tr key={s.strike} className={cn("border-t border-border/30", atm && "bg-primary/5")}>
                    <td className="p-1.5">
                      <div className="flex items-center gap-1.5">
                        <div className="h-2 rounded-sm bg-bear/40" style={{ width: `${(s.ceOi / maxOi) * 60}px` }} />
                        <span className="font-mono text-muted-foreground">{formatCompact(s.ceOi)}</span>
                      </div>
                    </td>
                    <td className={cn("p-1.5 text-center font-mono font-medium", atm && "text-primary")}>{s.strike}</td>
                    <td className="p-1.5">
                      <div className="flex items-center justify-end gap-1.5">
                        <span className="font-mono text-muted-foreground">{formatCompact(s.peOi)}</span>
                        <div className="h-2 rounded-sm bg-bull/40" style={{ width: `${(s.peOi / maxOi) * 60}px` }} />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[11px] text-muted-foreground">EOD open interest from NSE F&O bhavcopy{data.asOf ? ` · ${data.asOf}` : ""}. Not advice.</p>
      </CardContent>
    </Card>
  );
}
