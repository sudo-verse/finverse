import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowDownRight,
  ArrowUpRight,
  BrainCircuit,
  LineChart as LineChartIcon,
  RefreshCcw,
  SearchX,
  Sparkles,
  Trophy,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ChartCard, ChartSkeleton } from "@/components/shared/chart-card";
import { StockSearch } from "@/components/shared/stock-search";
import { SignalBadge } from "@/components/shared/signal-badge";
import { CHART_COLORS, axisStyle, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CorporatePanel } from "@/components/stock/corporate-panel";
import { NseInsights } from "@/components/stock/nse-insights";
import { FinancialsPanel } from "@/components/stock/financials-panel";
import { OwnershipTrendPanel } from "@/components/stock/ownership-trend";
import { ScorecardPanel } from "@/components/stock/scorecard-panel";
import { useCompetitors, useGenerateReport, useHistoryRange, useIntraday, useLiveQuote, useStock } from "@/hooks/queries";
import {
  formatCompact,
  formatFraction,
  formatINR,
  formatINRCompact,
  formatMaybe,
  stripHtml,
  timeAgo,
} from "@/lib/format";
import { cn } from "@/lib/utils";
import type { AIReport, SignalType } from "@/types";

const RANGES = [
  { label: "1D", days: 0, remote: false }, // live intraday from NSE
  { label: "1M", days: 22, remote: false },
  { label: "3M", days: 66, remote: false },
  { label: "6M", days: 132, remote: false },
  { label: "1Y", days: 365, remote: false },
  // beyond the DB's 1-year window — served by /stocks/{symbol}/history (yfinance)
  { label: "3Y", days: 0, remote: true },
  { label: "5Y", days: 0, remote: true },
  { label: "10Y", days: 0, remote: true },
  { label: "MAX", days: 0, remote: true },
];

function formatTick(ms: number): string {
  // NSE encodes intraday timestamps as IST wall-clock in a UTC epoch
  // (e.g. 09:15 IST open arrives as an epoch that reads 09:15 UTC).
  // Formatting in UTC therefore yields the correct market time; using
  // Asia/Kolkata would add a second +5:30 and shift the axis past 15:30.
  return new Date(ms).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  });
}

const DEFAULT_SYMBOL = "TCS";

export default function StockAnalysisPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const activeSymbol = symbol?.toUpperCase() ?? DEFAULT_SYMBOL;
  const { data: stock, isLoading, isError, error } = useStock(activeSymbol);
  const { data: competitors } = useCompetitors(activeSymbol);
  const { data: live } = useLiveQuote(activeSymbol);
  const [range, setRange] = useState("6M");
  const { data: intraday } = useIntraday(activeSymbol, range === "1D");
  const intradayUp =
    intraday && intraday.points.length > 1
      ? intraday.points[intraday.points.length - 1].price >= intraday.points[0].price
      : true;

  // Prefer the live NSE tick over the EOD close when available
  const price = live?.lastPrice ?? stock?.price ?? null;
  const change = live?.change ?? stock?.change ?? null;
  const changePct = live?.pChange != null ? live.pChange / 100 : (stock?.changePct ?? null);
  const dayLow = live?.dayLow ?? stock?.dayLow ?? null;
  const dayHigh = live?.dayHigh ?? stock?.dayHigh ?? null;

  // AI report: fetched on demand (Gemini call can take a while). Keyed by
  // symbol so navigating to another stock naturally shows no stale report.
  const reportMutation = useGenerateReport();
  const [reportBySymbol, setReportBySymbol] = useState<{ symbol: string; data: AIReport } | null>(null);
  const report = reportBySymbol?.symbol === activeSymbol ? reportBySymbol.data : null;

  const requestReport = (useCache: boolean) => {
    reportMutation.mutate(
      { symbol: activeSymbol, useCache },
      {
        onSuccess: (r) => {
          setReportBySymbol({ symbol: r.symbol, data: r });
          toast.success(r.cached ? `Loaded cached report for ${activeSymbol}` : `Report generated for ${activeSymbol}`);
        },
        onError: (e) => {
          const detail =
            (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            "Report generation failed";
          toast.error(detail);
        },
      },
    );
  };

  const isRemoteRange = RANGES.find((r) => r.label === range)?.remote ?? false;
  const { data: remoteHistory } = useHistoryRange(activeSymbol, range, isRemoteRange);

  const visibleHistory = useMemo(() => {
    if (isRemoteRange) return remoteHistory ?? [];
    if (!stock) return [];
    const days = RANGES.find((r) => r.label === range)?.days ?? 132;
    return stock.priceHistory.slice(-days);
  }, [stock, range, isRemoteRange, remoteHistory]);

  const quantItems = stock?.quant
    ? [
        { label: "Cumulative Return", value: formatFraction(stock.quant.cumulativeReturn), tone: (stock.quant.cumulativeReturn ?? 0) >= 0 ? "up" : "down" },
        { label: "Annualized Return", value: formatFraction(stock.quant.annualizedReturn), tone: (stock.quant.annualizedReturn ?? 0) >= 0 ? "up" : "down" },
        { label: "Volatility (ann.)", value: formatFraction(stock.quant.annualizedVolatility), tone: "plain" },
        { label: "Sharpe Ratio", value: formatMaybe(stock.quant.sharpeRatio), tone: (stock.quant.sharpeRatio ?? 0) >= 0 ? "up" : "down" },
        { label: "Max Drawdown", value: formatFraction(stock.quant.maxDrawdown), tone: "down" },
        { label: "Trend", value: stock.quant.trend?.replace("_", " ") ?? "—", tone: "plain" },
      ]
    : [];

  const fundamentalItems = stock?.fundamentals
    ? [
        { label: "Revenue Growth", value: formatFraction(stock.fundamentals.revenueGrowth), tone: (stock.fundamentals.revenueGrowth ?? 0) >= 0 ? "up" : "down" },
        { label: "Earnings Growth", value: formatFraction(stock.fundamentals.earningsGrowth), tone: (stock.fundamentals.earningsGrowth ?? 0) >= 0 ? "up" : "down" },
        { label: "Net Margin", value: formatFraction(stock.fundamentals.netProfitMargin), tone: "plain" },
        { label: "ROE", value: formatFraction(stock.fundamentals.roe), tone: "plain" },
        { label: "ROCE", value: formatFraction(stock.fundamentals.roce), tone: "plain" },
        { label: "P/E", value: formatMaybe(stock.fundamentals.peRatio, 1, "x"), tone: "plain" },
        { label: "P/B", value: formatMaybe(stock.fundamentals.pbRatio, 1, "x"), tone: "plain" },
        { label: "Debt / Equity", value: formatMaybe(stock.fundamentals.debtToEquity), tone: (stock.fundamentals.debtToEquity ?? 0) > 1 ? "down" : "plain" },
      ]
    : [];

  return (
    <div>
      <PageHeader
        title="Stock Analysis"
        description="Deep-dive into price action, fundamentals and AI research"
        actions={<StockSearch className="w-full sm:w-80" onSelect={(sym) => navigate(`/stocks/${sym}`)} />}
      />

      {/* Error state (unknown symbol / no price data) */}
      {isError && (
        <Card className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <SearchX className="h-10 w-10 text-muted-foreground/50" />
          <p className="text-sm font-medium">No analysis available for {activeSymbol}</p>
          <p className="max-w-md text-xs text-muted-foreground">
            {(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
              "This symbol has no price history yet."}
          </p>
        </Card>
      )}

      {/* Quote header */}
      {!isError &&
        (isLoading || !stock ? (
          <Skeleton className="h-32 w-full rounded-xl" />
        ) : (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="p-5 md:p-6">
              <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="font-mono text-2xl font-bold">{stock.symbol}</h2>
                    {stock.industry && (
                      <Badge variant="muted" className="normal-case tracking-normal">
                        {stock.industry}
                      </Badge>
                    )}
                    <Badge variant="secondary" className="normal-case tracking-normal">
                      NSE
                    </Badge>
                    {live && (
                      <Badge variant="bull" className="gap-1.5">
                        <span className="relative flex h-1.5 w-1.5">
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-bull opacity-60" />
                          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-bull" />
                        </span>
                        LIVE
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{stock.name}</p>
                </div>

                <div className="flex flex-wrap items-center gap-6">
                  <div>
                    <p className="font-mono text-3xl font-bold tabular">
                      {price !== null ? formatINR(price) : "—"}
                    </p>
                    {change !== null && changePct !== null && (
                      <p
                        className={cn(
                          "mt-0.5 flex items-center gap-1 font-mono text-sm tabular",
                          changePct >= 0 ? "text-bull" : "text-bear",
                        )}
                      >
                        {changePct >= 0 ? (
                          <ArrowUpRight className="h-4 w-4" />
                        ) : (
                          <ArrowDownRight className="h-4 w-4" />
                        )}
                        {formatINR(Math.abs(change))} ({formatFraction(changePct, 2)})
                      </p>
                    )}
                  </div>
                  <div className="hidden text-xs text-muted-foreground sm:block">
                    <p>
                      Day range ·{" "}
                      <span className="font-mono tabular text-foreground">
                        {formatMaybe(dayLow)} – {formatMaybe(dayHigh)}
                      </span>
                    </p>
                    <p className="mt-1">
                      52W range ·{" "}
                      <span className="font-mono tabular text-foreground">
                        {formatMaybe(stock.week52Low)} – {formatMaybe(stock.week52High)}
                      </span>
                    </p>
                    {live && (
                      <p className="mt-1">
                        M.Cap{" "}
                        <span className="font-mono tabular text-foreground">
                          {live.marketCap !== null ? formatINRCompact(live.marketCap) : "—"}
                        </span>
                        {" · "}VWAP{" "}
                        <span className="font-mono tabular text-foreground">{formatMaybe(live.averagePrice)}</span>
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-start gap-1.5 rounded-xl border border-border/60 bg-secondary/40 px-4 py-3">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Engine Signal
                    </span>
                    <div className="flex items-center gap-2">
                      <SignalBadge signal={stock.recommendation as SignalType} />
                      <span className="font-mono text-xs tabular text-muted-foreground">
                        {stock.recommendationConfidence !== null
                          ? `${Math.round(stock.recommendationConfidence * 100)}% confidence`
                          : "trend-derived"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}

      {!isError && (
        <>
          {/* Price + volume charts */}
          <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
            <ChartCard
              title="Price Chart"
              description={range === "1D" ? "Live intraday ticks · NSE" : "Close price with SMA 20 / 50 / 200 overlays"}
              className="xl:col-span-2"
              delay={0.05}
              actions={
                <Tabs value={range} onValueChange={setRange}>
                  <TabsList>
                    {RANGES.map((r) => (
                      <TabsTrigger key={r.label} value={r.label}>
                        {r.label}
                      </TabsTrigger>
                    ))}
                  </TabsList>
                </Tabs>
              }
            >
              {range === "1D" ? (
                !intraday ? (
                  <ChartSkeleton height={320} />
                ) : intraday.points.length === 0 ? (
                  <div className="flex h-[320px] items-center justify-center text-sm text-muted-foreground">
                    No intraday data available
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={344}>
                    <ComposedChart data={intraday.points} margin={{ left: 4, right: 8 }}>
                      <defs>
                        <linearGradient id="gIntraday" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={intradayUp ? CHART_COLORS.green : CHART_COLORS.rose} stopOpacity={0.28} />
                          <stop offset="100%" stopColor={intradayUp ? CHART_COLORS.green : CHART_COLORS.rose} stopOpacity={0} />
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
                      <YAxis {...axisStyle} domain={["auto", "auto"]} width={56} tickFormatter={(v: number) => formatCompact(v)} />
                      <Tooltip
                        {...tooltipStyle}
                        labelFormatter={(v) => formatTick(Number(v))}
                        formatter={(v) => [formatINR(Number(v)), "Price"]}
                      />
                      <Area
                        type="monotone"
                        dataKey="price"
                        name="Price"
                        stroke={intradayUp ? CHART_COLORS.green : CHART_COLORS.rose}
                        strokeWidth={2}
                        fill="url(#gIntraday)"
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                )
              ) : isLoading || !stock ? (
                <ChartSkeleton height={320} />
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={320}>
                    <ComposedChart data={visibleHistory} margin={{ left: 4, right: 8 }}>
                      <defs>
                        <linearGradient id="gPrice" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={CHART_COLORS.blue} stopOpacity={0.28} />
                          <stop offset="100%" stopColor={CHART_COLORS.blue} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid {...gridStyle} />
                      <XAxis dataKey="date" {...axisStyle} minTickGap={40} tickFormatter={(d: string) => d.slice(5)} />
                      <YAxis {...axisStyle} domain={["auto", "auto"]} width={56} tickFormatter={(v: number) => formatCompact(v)} />
                      <Tooltip
                        {...tooltipStyle}
                        formatter={(v, name) => [v == null ? "—" : formatINR(Number(v)), name]}
                      />
                      <Area type="monotone" dataKey="close" name="Close" stroke={CHART_COLORS.blue} strokeWidth={2} fill="url(#gPrice)" />
                      <Line type="monotone" dataKey="sma20" name="SMA 20" stroke={CHART_COLORS.cyan} strokeWidth={1.3} dot={false} />
                      <Line type="monotone" dataKey="sma50" name="SMA 50" stroke={CHART_COLORS.amber} strokeWidth={1.3} dot={false} />
                      <Line type="monotone" dataKey="sma200" name="SMA 200" stroke={CHART_COLORS.violet} strokeWidth={1.3} dot={false} />
                    </ComposedChart>
                  </ResponsiveContainer>
                  <div className="mt-2 flex flex-wrap justify-center gap-4 text-[11px] text-muted-foreground">
                    {[
                      { label: "Close", color: CHART_COLORS.blue },
                      { label: "SMA 20", color: CHART_COLORS.cyan },
                      { label: "SMA 50", color: CHART_COLORS.amber },
                      { label: "SMA 200", color: CHART_COLORS.violet },
                    ].map((l) => (
                      <span key={l.label} className="flex items-center gap-1.5">
                        <span className="h-0.5 w-4 rounded-full" style={{ background: l.color }} />
                        {l.label}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </ChartCard>

            <div className="flex flex-col gap-4">
              <ChartCard title="Volume" description="Daily traded volume" delay={0.1}>
                {isLoading || !stock ? (
                  <ChartSkeleton height={150} />
                ) : (
                  <ResponsiveContainer width="100%" height={150}>
                    <BarChart data={visibleHistory} margin={{ left: 4, right: 8 }}>
                      <CartesianGrid {...gridStyle} />
                      <XAxis dataKey="date" {...axisStyle} minTickGap={50} tickFormatter={(d: string) => d.slice(5)} />
                      <YAxis {...axisStyle} width={44} tickFormatter={(v: number) => formatCompact(v)} />
                      <Tooltip {...tooltipStyle} cursor={{ fill: "rgba(140,165,200,0.06)" }} />
                      <Bar dataKey="volume" name="Volume" fill={CHART_COLORS.slate} radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              {/* Quant + fundamentals */}
              <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
                <Card className="glass-hover flex-1">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <LineChartIcon className="h-4 w-4 text-primary" /> Key Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {isLoading || !stock ? (
                      <Skeleton className="h-40 w-full" />
                    ) : (
                      <>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                          {quantItems.map((f) => (
                            <MetricTile key={f.label} {...f} />
                          ))}
                        </div>
                        {fundamentalItems.length > 0 ? (
                          <>
                            <p className="pt-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                              Fundamentals · {stock.fundamentals?.period}
                            </p>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                              {fundamentalItems.map((f) => (
                                <MetricTile key={f.label} {...f} />
                              ))}
                            </div>
                          </>
                        ) : (
                          <p className="text-xs text-muted-foreground">
                            No fundamentals loaded for this symbol yet (
                            <code className="font-mono">python -m app.etl.financials_etl</code>).
                          </p>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>

          {/* Fundamentals terminal: CAGR, statements, ratio trends, pros & cons */}
          {stock && <ScorecardPanel symbol={activeSymbol} />}

          {stock && <FinancialsPanel symbol={activeSymbol} />}

          {stock && <OwnershipTrendPanel symbol={activeSymbol} />}

          {/* AI report + competitor snapshot */}
          <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="xl:col-span-2"
            >
              <Card className="glass-hover h-full">
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle className="flex items-center gap-2">
                    <BrainCircuit className="h-4 w-4 text-chart-4" /> AI Investment Report
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    {report?.generatedAt && (
                      <span className="text-[11px] text-muted-foreground">
                        {report.cached ? "cached · " : ""}
                        {timeAgo(report.generatedAt)} · {report.model}
                      </span>
                    )}
                    {report && (
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={reportMutation.isPending}
                        onClick={() => requestReport(false)}
                      >
                        <RefreshCcw className={cn(reportMutation.isPending && "animate-spin")} /> Regenerate
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {report ? (
                    <div className="prose-finverse text-sm leading-relaxed">
                      <ReactMarkdown>{report.reportMd}</ReactMarkdown>
                    </div>
                  ) : reportMutation.isPending ? (
                    <div className="space-y-3 py-2">
                      <Skeleton className="h-4 w-2/5" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-11/12" />
                      <Skeleton className="h-4 w-4/5" />
                      <p className="pt-2 text-xs text-muted-foreground">Generating with Gemini — this can take ~20s…</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-3 py-10 text-center">
                      <Sparkles className="h-8 w-8 text-chart-4/60" />
                      <p className="text-sm text-muted-foreground">
                        Generate an evidence-based investment summary from the stock's metrics, fundamentals, peer
                        ranking and recent signals.
                      </p>
                      <Button onClick={() => requestReport(true)} disabled={reportMutation.isPending}>
                        <Sparkles /> Generate report
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Competitor snapshot (live peer ranks) */}
            <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
              <Card className="glass-hover h-full">
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="h-4 w-4 text-hold" /> Competitor Snapshot
                  </CardTitle>
                  <Link to={`/competitors/${activeSymbol}`} className="text-xs font-medium text-primary hover:underline">
                    Full analysis →
                  </Link>
                </CardHeader>
                <CardContent>
                  {!competitors ? (
                    <Skeleton className="h-56 w-full" />
                  ) : (
                    <>
                      <div className="mb-4 flex items-center gap-3 rounded-xl bg-secondary/40 px-4 py-3">
                        <span className="font-mono text-2xl font-bold text-hold">
                          {competitors.overallRank !== null ? `#${competitors.overallRank}` : "—"}
                        </span>
                        <div className="text-xs text-muted-foreground">
                          <p className="font-medium text-foreground">Rank in {competitors.industry}</p>
                          <p>of {competitors.peerCount} peers with data · avg of metric ranks</p>
                        </div>
                      </div>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Metric</TableHead>
                            <TableHead className="text-right">Value</TableHead>
                            <TableHead className="text-right">Peer Avg</TableHead>
                            <TableHead className="text-right">Rank</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {competitors.comparison.slice(0, 6).map((c) => (
                            <TableRow key={c.metric}>
                              <TableCell className="text-xs capitalize">{c.metric.replace(/_/g, " ")}</TableCell>
                              <TableCell className="text-right font-mono text-xs tabular">
                                {formatMetricValue(c.metric, c.value)}
                              </TableCell>
                              <TableCell className="text-right font-mono text-xs tabular">
                                {formatMetricValue(c.metric, c.peerAvg)}
                              </TableCell>
                              <TableCell className="text-right font-mono text-xs tabular">
                                {c.rank ? `${c.rank}/${c.outOf}` : "—"}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Shareholding, returns vs index, exchange profile — live from NSE */}
          {stock && <NseInsights symbol={activeSymbol} />}

          {/* Corporate filings, events, results — live from NSE */}
          {stock && (
            <div className="mt-6">
              <CorporatePanel symbol={activeSymbol} />
            </div>
          )}

          {/* Recent signals for this stock */}
          {stock && stock.recentSignals.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="mt-6">
              <Card className="glass-hover">
                <CardHeader>
                  <CardTitle>Recent Signals · {stock.symbol}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1">
                  {stock.recentSignals.map((s) => (
                    <div key={s.id} className="flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-accent/50">
                      <SignalBadge signal={s.signal as SignalType} />
                      <p className="min-w-0 flex-1 truncate text-sm text-foreground/90">{stripHtml(s.eventTitle)}</p>
                      <span className="shrink-0 text-[11px] text-muted-foreground">
                        {s.source} · {s.timestamp ? timeAgo(s.timestamp) : ""}
                      </span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
}

/* ----------------------------- small helpers ----------------------------- */

const PERCENT_METRICS = new Set([
  "revenue_growth", "earnings_growth", "net_profit_margin", "roe", "roce",
  "cumulative_return", "annualized_volatility",
]);

function formatMetricValue(metric: string, value: number | null): string {
  if (value === null) return "—";
  if (PERCENT_METRICS.has(metric)) return formatFraction(value);
  return formatMaybe(value);
}

function MetricTile({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="rounded-lg bg-secondary/40 px-3 py-2.5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
      <p
        className={cn(
          "mt-0.5 font-mono text-sm font-semibold tabular capitalize",
          tone === "up" && "text-bull",
          tone === "down" && "text-bear",
        )}
      >
        {value}
      </p>
    </div>
  );
}
