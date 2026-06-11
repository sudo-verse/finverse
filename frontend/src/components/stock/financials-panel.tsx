import { useMemo } from "react";
import { motion } from "framer-motion";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download, RefreshCw, Sparkles, ThumbsDown, ThumbsUp, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { CHART_COLORS, tooltipStyle } from "@/components/shared/chart-theme";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCagr, useProsCons, useRatios, useRefreshProsCons, useStatements } from "@/hooks/queries";
import { formatCompact, formatFraction } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ProsConsItem, StatementRow } from "@/types";

/* Note: yfinance reports statements in the company's filing currency (some
 * NSE companies file in USD), so values are shown as plain compact numbers
 * with no ₹ symbol. Growth %, ratios and CAGR are currency-agnostic. */

function Growth({ value }: { value: number | null }) {
  if (value === null) return <span className="text-muted-foreground/60">—</span>;
  return (
    <span className={cn("font-mono text-[11px] tabular", value >= 0 ? "text-bull" : "text-bear")}>
      {formatFraction(value)}
    </span>
  );
}

function exportCsv(rows: StatementRow[], symbol: string) {
  const cols = ["period", "revenue", "netIncome", "ebit", "eps", "totalAssets", "totalEquity", "operatingCashFlow"] as const;
  const csv = [
    cols.join(","),
    ...rows.map((r) => cols.map((c) => r[c] ?? "").join(",")),
  ].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: `${symbol}-financials.csv` });
  a.click();
  URL.revokeObjectURL(url);
  toast.success("Financials exported as CSV");
}

const RATIO_DEFS = [
  { key: "roe", label: "ROE", color: CHART_COLORS.green },
  { key: "roce", label: "ROCE", color: CHART_COLORS.cyan },
  { key: "opm", label: "OPM", color: CHART_COLORS.amber },
  { key: "npm", label: "NPM", color: CHART_COLORS.violet },
  { key: "debtToEquity", label: "Debt / Equity", color: CHART_COLORS.rose },
] as const;

function ConfidenceBar({ value }: { value: number }) {
  return (
    <span className="ml-auto flex shrink-0 items-center gap-1.5" title={`Confidence ${Math.round(value * 100)}%`}>
      <span className="h-1 w-12 overflow-hidden rounded-full bg-muted">
        <span className="block h-full rounded-full bg-primary" style={{ width: `${Math.round(value * 100)}%` }} />
      </span>
      <span className="font-mono text-[10px] tabular text-muted-foreground">{Math.round(value * 100)}%</span>
    </span>
  );
}

function ProsConsList({ items, positive }: { items: ProsConsItem[]; positive: boolean }) {
  const Icon = positive ? ThumbsUp : ThumbsDown;
  return (
    <div className="space-y-2">
      <p className={cn("flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider", positive ? "text-bull" : "text-bear")}>
        <Icon className="h-3.5 w-3.5" /> {positive ? "Pros" : "Cons"}
      </p>
      {items.map((it) => (
        <div key={it.point} className="flex items-start gap-2 rounded-lg bg-secondary/40 px-3 py-2 text-xs leading-relaxed">
          <span className={cn("mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full", positive ? "bg-bull" : "bg-bear")} />
          <span className="text-foreground/85">{it.point}</span>
          <ConfidenceBar value={it.confidence} />
        </div>
      ))}
    </div>
  );
}

/** Screener-style fundamentals block: CAGR cards, annual statements with YoY
 *  growth + CSV export, ratio trend charts and AI pros/cons. */
export function FinancialsPanel({ symbol }: { symbol: string }) {
  const { data: statements, isLoading: stmtLoading, isError: stmtError } = useStatements(symbol);
  const { data: ratios } = useRatios(symbol);
  const { data: cagr } = useCagr(symbol);
  const { data: prosCons, isLoading: pcLoading } = useProsCons(symbol);
  const refreshPc = useRefreshProsCons();

  const ratioData = useMemo(
    () => (ratios ?? []).map((r) => ({ ...r, period: r.period.replace("FY", "") })),
    [ratios],
  );

  return (
    <div className="mt-6 space-y-4">
      {/* CAGR cards */}
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="glass-hover">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" /> Compounded Growth (CAGR)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!cagr ? (
              <Skeleton className="h-24 w-full" />
            ) : (
              <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
                {cagr.map((row) => (
                  <div key={row.metric} className="rounded-lg bg-secondary/40 px-3 py-2.5">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{row.metric}</p>
                    <div className="mt-1.5 space-y-0.5">
                      {([["1Y", row.y1], ["3Y", row.y3], ["5Y", row.y5], ["10Y", row.y10]] as const).map(([label, v]) => (
                        <div key={label} className="flex items-baseline justify-between">
                          <span className="text-[10px] text-muted-foreground">{label}</span>
                          {v === null ? (
                            <span className="font-mono text-xs text-muted-foreground/50">—</span>
                          ) : (
                            <span className={cn("font-mono text-xs font-semibold tabular", v >= 0 ? "text-bull" : "text-bear")}>
                              {formatFraction(v)}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Annual statements */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="xl:col-span-2">
          <Card className="glass-hover h-full">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Annual Financials</CardTitle>
              {statements && statements.length > 0 && (
                <Button variant="outline" size="sm" onClick={() => exportCsv(statements, symbol)}>
                  <Download className="h-3.5 w-3.5" /> CSV
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {stmtLoading ? (
                <Skeleton className="h-48 w-full" />
              ) : stmtError || !statements || statements.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  No financial statements for {symbol} yet — run{" "}
                  <code className="rounded bg-muted px-1 py-0.5 text-xs">python -m app.etl.financials_etl</code>
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border/60 text-left text-[10px] uppercase tracking-wider text-muted-foreground">
                        <th className="py-2 pr-3">Metric</th>
                        {statements.map((s) => (
                          <th key={s.period} className="py-2 pr-3 text-right font-mono">{s.period}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="[&_td]:py-2 [&_td]:pr-3">
                      {([
                        ["Revenue", (s: StatementRow) => s.revenue, (s: StatementRow) => s.revenueGrowth],
                        ["Net Profit", (s: StatementRow) => s.netIncome, (s: StatementRow) => s.netIncomeGrowth],
                        ["EBIT", (s: StatementRow) => s.ebit, null],
                        ["EPS", (s: StatementRow) => s.eps, (s: StatementRow) => s.epsGrowth],
                        ["Total Assets", (s: StatementRow) => s.totalAssets, null],
                        ["Equity", (s: StatementRow) => s.totalEquity, null],
                        ["Op. Cash Flow", (s: StatementRow) => s.operatingCashFlow, null],
                      ] as const).map(([label, getter, growthGetter]) => (
                        <tr key={label} className="border-b border-border/40 last:border-0">
                          <td className="font-medium text-muted-foreground">{label}</td>
                          {statements.map((s) => {
                            const v = getter(s);
                            return (
                              <td key={s.period} className="text-right">
                                <span className="font-mono tabular">{v === null ? "—" : formatCompact(v)}</span>
                                {growthGetter && (
                                  <div><Growth value={growthGetter(s)} /></div>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="mt-2 text-[10px] text-muted-foreground/70">
                    Values in the company's filing currency (via Yahoo Finance). Sub-figures show YoY growth.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Ratio trends */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
          <Card className="glass-hover h-full">
            <CardHeader>
              <CardTitle>Ratio Trends</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!ratios ? (
                <Skeleton className="h-48 w-full" />
              ) : ratioData.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">No ratio history available.</p>
              ) : (
                RATIO_DEFS.map(({ key, label, color }) => {
                  const hasData = ratioData.some((r) => r[key] !== null);
                  if (!hasData) return null;
                  const latest = [...ratioData].reverse().find((r) => r[key] !== null);
                  const isDE = key === "debtToEquity";
                  return (
                    <div key={key} className="flex items-center gap-3 rounded-lg bg-secondary/40 px-3 py-2">
                      <div className="w-24 shrink-0">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
                        <p className="font-mono text-sm font-semibold tabular">
                          {latest?.[key] === null || latest?.[key] === undefined
                            ? "—"
                            : isDE
                              ? latest[key]!.toFixed(2)
                              : formatFraction(latest[key])}
                        </p>
                      </div>
                      <ResponsiveContainer width="100%" height={42}>
                        <LineChart data={ratioData} margin={{ top: 4, bottom: 0, left: 0, right: 0 }}>
                          <XAxis dataKey="period" hide />
                          <YAxis hide domain={["auto", "auto"]} />
                          <Tooltip
                            {...tooltipStyle}
                            formatter={(v) => [isDE ? Number(v).toFixed(2) : formatFraction(Number(v)), label]}
                            labelFormatter={(p) => `FY${p}`}
                          />
                          <Line type="monotone" dataKey={key} stroke={color} strokeWidth={1.6} dot={{ r: 2 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* AI Pros & Cons */}
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card className="glass-hover">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" /> Pros & Cons
              <span className="text-[10px] font-normal normal-case tracking-normal text-muted-foreground">
                AI-generated from financials, signals & peers
              </span>
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              disabled={refreshPc.isPending}
              onClick={() =>
                refreshPc.mutate(symbol, {
                  onError: () => toast.error("Could not regenerate pros & cons"),
                })
              }
            >
              <RefreshCw className={cn("h-3.5 w-3.5", refreshPc.isPending && "animate-spin")} />
              {prosCons ? "Regenerate" : "Generate"}
            </Button>
          </CardHeader>
          <CardContent>
            {pcLoading || refreshPc.isPending ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-32 w-full" />
              </div>
            ) : !prosCons ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Click <span className="font-medium text-foreground">Generate</span> to build an AI pros/cons assessment.
              </p>
            ) : (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <ProsConsList items={prosCons.pros} positive />
                <ProsConsList items={prosCons.cons} positive={false} />
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
