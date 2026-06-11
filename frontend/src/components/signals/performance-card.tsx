import { useQuery } from "@tanstack/react-query";
import { FlaskConical } from "lucide-react";
import { apiClient } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatFraction } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { SignalPerformance } from "@/types";

function useSignalPerformance() {
  return useQuery({
    queryKey: ["signal-performance"],
    queryFn: async () => (await apiClient.get<SignalPerformance>("/signals/performance")).data,
    staleTime: 10 * 60_000,
  });
}

/** Backtest summary: does the engine's advice actually make money? */
export function PerformanceCard() {
  const { data, isLoading } = useSignalPerformance();

  return (
    <Card className="glass-hover mb-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FlaskConical className="h-4 w-4 text-chart-4" /> Signal Track Record
          <span className="text-[10px] font-normal normal-case tracking-normal text-muted-foreground">
            forward returns after each BUY/SELL · no costs
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : !data || data.evaluated === 0 ? (
          <p className="py-3 text-center text-xs text-muted-foreground">
            Not enough history yet — signals need at least 7 days of forward prices before they can be judged. This
            fills in automatically as the engine runs.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {data.rows.map((r) => (
              <div key={r.signal} className="rounded-xl bg-secondary/40 px-4 py-3">
                <div className="flex items-baseline justify-between">
                  <span className={cn("text-sm font-bold", r.signal === "BUY" ? "text-bull" : "text-bear")}>
                    {r.signal}
                  </span>
                  <span className="font-mono text-[11px] tabular text-muted-foreground">{r.count} signals</span>
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-center">
                  {(
                    [
                      ["Hit rate", r.hitRate],
                      ["Avg 7d", r.avgReturn7D],
                      ["Avg 30d", r.avgReturn30D],
                    ] as const
                  ).map(([label, v]) => (
                    <div key={label}>
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
                      <p
                        className={cn(
                          "font-mono text-sm font-semibold tabular",
                          v !== null && label !== "Hit rate" && (v >= 0 ? "text-bull" : "text-bear"),
                        )}
                      >
                        {v === null ? "—" : formatFraction(v)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
