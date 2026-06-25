import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, Landmark } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { axisStyle, CHART_COLORS, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketFlows } from "@/hooks/queries";
import { cn } from "@/lib/utils";

/** ₹ crore with Indian grouping and a sign, e.g. +₹3,107 Cr / −₹2,418 Cr. */
function fmtCr(v: number | null | undefined): string {
  if (v == null) return "—";
  const sign = v >= 0 ? "+" : "−";
  const n = Math.abs(Math.round(v)).toLocaleString("en-IN");
  return `${sign}₹${n} Cr`;
}

function shortDate(d: string): string {
  const dt = new Date(d);
  return dt.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

function NetStat({ label, net, buy, sell }: { label: string; net: number | null; buy: number | null; sell: number | null }) {
  const up = (net ?? 0) >= 0;
  return (
    <div className="rounded-xl border border-border/60 bg-card/40 p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        <Badge variant={up ? "bull" : "bear"} className="gap-1">
          {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
          {up ? "Net Buy" : "Net Sell"}
        </Badge>
      </div>
      <div className={cn("mt-1 font-mono text-2xl font-bold tabular", up ? "text-bull" : "text-bear")}>
        {fmtCr(net)}
      </div>
      <div className="mt-1 text-xs text-muted-foreground">
        Buy ₹{buy != null ? Math.round(buy).toLocaleString("en-IN") : "—"} ·
        {" "}Sell ₹{sell != null ? Math.round(sell).toLocaleString("en-IN") : "—"}
      </div>
    </div>
  );
}

export function InstitutionalFlows() {
  const { data, isLoading } = useMarketFlows(30);
  const latest = data?.latest;
  const chart = (data?.history ?? []).map((r) => ({
    date: shortDate(r.date),
    fii: r.fiiNet,
    dii: r.diiNet,
  }));

  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.16 }} className="mt-6">
      <Card className="glass-hover">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <Landmark className="h-4 w-4 text-primary" /> Institutional Flows
            {latest && (
              <span className="text-xs font-normal text-muted-foreground">· {shortDate(latest.date)} (cash, provisional)</span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-56 w-full rounded-lg" />
          ) : !latest ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No FII/DII flow data yet — the daily ETL populates this after market close.
            </p>
          ) : (
            <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
              <div className="space-y-3">
                <NetStat label="FII / FPI" net={latest.fiiNet} buy={latest.fiiBuy} sell={latest.fiiSell} />
                <NetStat label="DII" net={latest.diiNet} buy={latest.diiBuy} sell={latest.diiSell} />
                {data && data.windowDays > 1 && (
                  <div className="flex items-center justify-between rounded-lg bg-secondary/40 px-3 py-2 text-xs">
                    <span className="text-muted-foreground">{data.windowDays}-day net</span>
                    <span className="font-mono tabular">
                      <span className={cn((data.fiiNetWindow ?? 0) >= 0 ? "text-bull" : "text-bear")}>
                        FII {fmtCr(data.fiiNetWindow)}
                      </span>
                      <span className="mx-1 text-muted-foreground">·</span>
                      <span className={cn((data.diiNetWindow ?? 0) >= 0 ? "text-bull" : "text-bear")}>
                        DII {fmtCr(data.diiNetWindow)}
                      </span>
                    </span>
                  </div>
                )}
              </div>

              <div className="h-64 w-full">
                {chart.length < 2 ? (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    History builds up daily — check back after a few sessions.
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chart} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                      <CartesianGrid {...gridStyle} />
                      <XAxis dataKey="date" {...axisStyle} interval="preserveStartEnd" minTickGap={24} />
                      <YAxis {...axisStyle} width={48} tickFormatter={(v) => `${v / 1000}k`} />
                      <ReferenceLine y={0} stroke="rgba(140,165,200,0.35)" />
                      <Tooltip {...tooltipStyle} formatter={(v, name) => [fmtCr(Number(v)), name === "fii" ? "FII" : "DII"]} />
                      <Bar dataKey="fii" name="fii" radius={[2, 2, 0, 0]} barSize={5}>
                        {chart.map((d, i) => (
                          <Cell key={`f${i}`} fill={(d.fii ?? 0) >= 0 ? CHART_COLORS.blue : CHART_COLORS.rose} />
                        ))}
                      </Bar>
                      <Bar dataKey="dii" name="dii" radius={[2, 2, 0, 0]} barSize={5}>
                        {chart.map((d, i) => (
                          <Cell key={`d${i}`} fill={(d.dii ?? 0) >= 0 ? CHART_COLORS.green : CHART_COLORS.amber} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
