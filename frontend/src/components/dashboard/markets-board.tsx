import { useState } from "react";
import { motion } from "framer-motion";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CandlestickChart, Globe2 } from "lucide-react";
import { ChartCard, ChartSkeleton } from "@/components/shared/chart-card";
import { CHART_COLORS, axisStyle, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAllIndices, useIndexChart, useTurnover } from "@/hooks/queries";
import { formatINRCompact, formatNumber, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

function formatTick(ms: number): string {
  // NSE encodes intraday timestamps as IST wall-clock in a UTC epoch
  // (09:15 IST open arrives as an epoch reading 09:15 UTC). Formatting in
  // UTC yields the correct market time; Asia/Kolkata would double-shift it.
  return new Date(ms).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  });
}

/** Live index chart + indices board + turnover summary (all NSE NextApi). */
export function MarketsBoard() {
  const [index, setIndex] = useState("NIFTY 50");
  const { data: indices } = useAllIndices();
  const { data: chart } = useIndexChart(index);
  const { data: turnover } = useTurnover();

  const chartUp =
    chart && chart.points.length > 1 ? chart.points[chart.points.length - 1].price >= chart.points[0].price : true;
  const color = chartUp ? CHART_COLORS.green : CHART_COLORS.rose;

  return (
    <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
      {/* Index intraday chart */}
      <ChartCard
        title="Index Chart"
        description="Live intraday · NSE"
        className="xl:col-span-2"
        delay={0.03}
        actions={
          <Select value={index} onValueChange={setIndex}>
            <SelectTrigger className="h-8 w-44 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(indices ?? [{ name: "NIFTY 50" }]).map((i) => (
                <SelectItem key={i.name} value={i.name}>
                  {i.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      >
        {!chart ? (
          <ChartSkeleton height={250} />
        ) : chart.points.length === 0 ? (
          <div className="flex h-[250px] items-center justify-center text-sm text-muted-foreground">
            No intraday data for {index}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chart.points} margin={{ left: 4, right: 8 }}>
              <defs>
                <linearGradient id="gIndex" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.25} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid {...gridStyle} />
              <XAxis
                dataKey="time"
                type="number"
                domain={["dataMin", "dataMax"]}
                scale="time"
                {...axisStyle}
                minTickGap={60}
                tickFormatter={formatTick}
              />
              <YAxis {...axisStyle} domain={["auto", "auto"]} width={64} tickFormatter={(v: number) => formatNumber(v, 0)} />
              <Tooltip
                {...tooltipStyle}
                labelFormatter={(v) => formatTick(Number(v))}
                formatter={(v) => [formatNumber(Number(v), 2), index]}
              />
              <Area type="monotone" dataKey="price" stroke={color} strokeWidth={2} fill="url(#gIndex)" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <div className="flex flex-col gap-4">
        {/* Indices board */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.06 }}>
          <Card className="glass-hover">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe2 className="h-4 w-4 text-primary" /> Indices
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!indices ? (
                <Skeleton className="h-36 w-full" />
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  {indices.slice(0, 6).map((i) => (
                    <button
                      key={i.name}
                      type="button"
                      onClick={() => setIndex(i.name)}
                      className={cn(
                        "cursor-pointer rounded-lg border border-transparent bg-secondary/40 px-3 py-2 text-left transition-colors hover:border-primary/40",
                        i.name === index && "border-primary/50 bg-primary/10",
                      )}
                    >
                      <p className="truncate text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                        {i.name}
                      </p>
                      <p className="mt-0.5 font-mono text-sm font-semibold tabular">
                        {i.last !== null ? formatNumber(i.last, 2) : "—"}
                      </p>
                      <p
                        className={cn(
                          "font-mono text-[11px] tabular",
                          (i.percChange ?? 0) >= 0 ? "text-bull" : "text-bear",
                        )}
                      >
                        {i.percChange !== null ? formatPercent(i.percChange) : "—"}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Turnover summary */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.09 }}>
          <Card className="glass-hover flex-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CandlestickChart className="h-4 w-4 text-chart-4" /> Market Turnover
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!turnover ? (
                <Skeleton className="h-24 w-full" />
              ) : (
                <div className="space-y-2">
                  {turnover
                    .filter((t) => t.turnover !== null)
                    .slice(0, 3)
                    .map((t) => {
                      const delta =
                        t.turnover !== null && t.prevTurnover
                          ? ((t.turnover - t.prevTurnover) / t.prevTurnover) * 100
                          : null;
                      return (
                        <div key={`${t.segment}-${t.instrument}`} className="flex items-center justify-between rounded-lg bg-secondary/40 px-3 py-2">
                          <div>
                            <p className="text-xs font-medium">{t.instrument}</p>
                            <p className="text-[10px] text-muted-foreground">
                              {t.trades !== null ? `${formatNumber(t.trades, 0)} trades` : ""}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="font-mono text-sm font-semibold tabular">
                              {t.turnover !== null ? formatINRCompact(t.turnover) : "—"}
                            </p>
                            {delta !== null && (
                              <p className={cn("font-mono text-[11px] tabular", delta >= 0 ? "text-bull" : "text-bear")}>
                                {formatPercent(delta, 1)} vs prev
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
