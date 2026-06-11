import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SearchX, Trophy } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ChartCard, ChartSkeleton } from "@/components/shared/chart-card";
import { StockSearch } from "@/components/shared/stock-search";
import { CHART_COLORS, axisStyle, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCompetitors, useLivePeers, usePeerQuarters } from "@/hooks/queries";
import { formatFraction, formatINRCompact, formatMaybe, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { PeerRow } from "@/types";

const RADAR_COLORS = [CHART_COLORS.blue, CHART_COLORS.green, CHART_COLORS.amber, CHART_COLORS.violet];
const DEFAULT_SYMBOL = "TCS";

/** Build normalized 0–100 radar scores from real peer metrics. */
function buildRadar(peers: PeerRow[], target: string) {
  const withData = peers.filter(
    (p) => p.roe !== null || p.revenueGrowth !== null || p.sharpeRatio !== null,
  );
  // target first, then the strongest peers by ROE
  const selected = [
    ...withData.filter((p) => p.symbol === target),
    ...withData.filter((p) => p.symbol !== target).sort((a, b) => (b.roe ?? -1) - (a.roe ?? -1)),
  ].slice(0, 4);

  const axes: { metric: string; get: (p: PeerRow) => number | null; invert?: boolean }[] = [
    { metric: "ROE", get: (p) => p.roe },
    { metric: "Rev Growth", get: (p) => p.revenueGrowth },
    { metric: "Net Margin", get: (p) => p.netProfitMargin },
    { metric: "Sharpe", get: (p) => p.sharpeRatio },
    { metric: "Low Leverage", get: (p) => p.debtToEquity, invert: true },
  ];

  const rows = axes.map(({ metric, get, invert }) => {
    const values = selected.map((p) => get(p)).filter((v): v is number => v !== null);
    const max = Math.max(...values, 0);
    const min = Math.min(...values, 0);
    const span = max - min || 1;
    const row: Record<string, string | number> = { metric };
    for (const p of selected) {
      const v = get(p);
      if (v === null) {
        row[p.symbol] = 0;
      } else {
        const norm = (v - min) / span; // 0..1 within the group
        row[p.symbol] = Math.round((invert ? 1 - norm : norm) * 100);
      }
    }
    return row;
  });
  return { rows, symbols: selected.map((p) => p.symbol) };
}

export default function CompetitorsPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const activeSymbol = symbol?.toUpperCase() ?? DEFAULT_SYMBOL;
  const { data, isLoading, isError, error } = useCompetitors(activeSymbol);
  const [quarter, setQuarter] = useState("");
  const { data: quarters } = usePeerQuarters(activeSymbol);
  const { data: livePeers } = useLivePeers(activeSymbol, quarter);

  const radar = useMemo(() => (data ? buildRadar(data.peers, data.symbol) : null), [data]);
  const roePeers = useMemo(
    () =>
      data
        ? [...data.peers].filter((p) => p.roe !== null).sort((a, b) => (b.roe ?? 0) - (a.roe ?? 0)).slice(0, 8)
        : [],
    [data],
  );
  const growthPeers = useMemo(
    () =>
      data
        ? [...data.peers]
            .filter((p) => p.revenueGrowth !== null)
            .sort((a, b) => (b.revenueGrowth ?? 0) - (a.revenueGrowth ?? 0))
            .slice(0, 8)
        : [],
    [data],
  );

  return (
    <div>
      <PageHeader
        title="Competitor Analysis"
        description="Peer benchmarking across valuation, growth and quality"
        actions={<StockSearch className="w-full sm:w-80" onSelect={(sym) => navigate(`/competitors/${sym}`)} />}
      />

      {isError && (
        <Card className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <SearchX className="h-10 w-10 text-muted-foreground/50" />
          <p className="text-sm font-medium">No peer analysis available for {activeSymbol}</p>
          <p className="max-w-md text-xs text-muted-foreground">
            {(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
              "This symbol has no industry mapping or analytics yet."}
          </p>
        </Card>
      )}

      {!isError && (isLoading || !data ? (
        <Skeleton className="h-24 w-full rounded-xl" />
      ) : (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between md:p-6">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-hold/10 text-hold">
                <Trophy className="h-7 w-7" />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="font-mono text-2xl font-bold">{data.symbol}</h2>
                  <Badge variant="muted" className="normal-case tracking-normal">
                    {data.industry}
                  </Badge>
                </div>
                <p className="mt-0.5 text-sm text-muted-foreground">{data.company}</p>
              </div>
            </div>
            <div className="flex gap-8">
              <div className="text-center">
                <p className="font-mono text-2xl font-bold text-hold">
                  {data.overallRank !== null ? `#${data.overallRank}` : "—"}
                </p>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Overall rank
                </p>
              </div>
              <div className="text-center">
                <p className="font-mono text-2xl font-bold">{data.peerCount}</p>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Peers with data
                </p>
              </div>
              <div className="text-center">
                <p className="font-mono text-2xl font-bold">{data.comparison.length}</p>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Metrics ranked
                </p>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}

      {!isError && (
        <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
          {/* Radar */}
          <ChartCard title="Quality Radar" description="Scores normalized within the peer group · larger is better" delay={0.05}>
            {isLoading || !radar ? (
              <ChartSkeleton height={320} />
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <RadarChart data={radar.rows} outerRadius="72%">
                  <PolarGrid stroke="rgba(140,165,200,0.12)" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: "#8294ab", fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  {radar.symbols.map((sym, i) => (
                    <Radar
                      key={sym}
                      name={sym}
                      dataKey={sym}
                      stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
                      fill={RADAR_COLORS[i % RADAR_COLORS.length]}
                      fillOpacity={sym === data?.symbol ? 0.25 : 0.06}
                      strokeWidth={sym === data?.symbol ? 2.5 : 1.5}
                    />
                  ))}
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Tooltip {...tooltipStyle} />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          {/* ROE bar comparison */}
          <ChartCard title="Return on Equity" description="ROE across peers (top 8)" delay={0.1}>
            {isLoading || !data ? (
              <ChartSkeleton height={320} />
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={roePeers.map((p) => ({ ...p, roePct: (p.roe ?? 0) * 100 }))} margin={{ left: -8, right: 8 }}>
                  <CartesianGrid {...gridStyle} />
                  <XAxis dataKey="symbol" {...axisStyle} />
                  <YAxis {...axisStyle} tickFormatter={(v: number) => `${v}%`} />
                  <Tooltip
                    {...tooltipStyle}
                    cursor={{ fill: "rgba(140,165,200,0.06)" }}
                    formatter={(v) => `${Number(v).toFixed(1)}%`}
                  />
                  <Bar dataKey="roePct" name="ROE" radius={[4, 4, 0, 0]} barSize={32}>
                    {roePeers.map((p) => (
                      <Cell
                        key={p.symbol}
                        fill={p.symbol === data.symbol ? CHART_COLORS.blue : CHART_COLORS.slate}
                        opacity={p.symbol === data.symbol ? 1 : 0.55}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          {/* Revenue growth ranking */}
          <ChartCard title="Revenue Growth Ranking" description="Latest-year revenue growth (top 8)" delay={0.15}>
            {isLoading || !data ? (
              <ChartSkeleton height={280} />
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart
                  data={growthPeers.map((p) => ({ ...p, growthPct: (p.revenueGrowth ?? 0) * 100 }))}
                  layout="vertical"
                  margin={{ left: 8, right: 24 }}
                >
                  <CartesianGrid {...gridStyle} horizontal={false} vertical />
                  <XAxis type="number" {...axisStyle} tickFormatter={(v: number) => `${v}%`} />
                  <YAxis type="category" dataKey="symbol" width={90} {...axisStyle} />
                  <Tooltip
                    {...tooltipStyle}
                    cursor={{ fill: "rgba(140,165,200,0.06)" }}
                    formatter={(v) => `${Number(v).toFixed(1)}%`}
                  />
                  <Bar dataKey="growthPct" name="Rev Growth" radius={[0, 4, 4, 0]} barSize={16}>
                    {growthPeers.map((p) => (
                      <Cell key={p.symbol} fill={p.symbol === data.symbol ? CHART_COLORS.green : CHART_COLORS.slate} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          {/* Rank vs peers table */}
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card className="glass-hover h-full">
              <CardHeader>
                <CardTitle>Rank vs Peers · {activeSymbol}</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading || !data ? (
                  <Skeleton className="h-60 w-full" />
                ) : (
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
                      {data.comparison.map((c) => (
                        <TableRow key={c.metric}>
                          <TableCell className="text-xs capitalize">{c.metric.replace(/_/g, " ")}</TableCell>
                          <TableCell className="text-right font-mono text-xs tabular">
                            {formatMetricValue(c.metric, c.value)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs tabular">
                            {formatMetricValue(c.metric, c.peerAvg)}
                          </TableCell>
                          <TableCell
                            className={cn(
                              "text-right font-mono text-xs tabular",
                              c.rank === 1 && "font-bold text-bull",
                            )}
                          >
                            {c.rank ? `${c.rank}/${c.outOf}` : "—"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Live NSE peer comparison */}
      {livePeers && livePeers.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.22 }} className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
          <ChartCard
            title="Market Cap · Live"
            description="NSE peer comparison — real-time market capitalisation"
          >
            <ResponsiveContainer width="100%" height={Math.max(200, livePeers.length * 34)}>
              <BarChart
                data={[...livePeers].sort((a, b) => (b.marketCap ?? 0) - (a.marketCap ?? 0))}
                layout="vertical"
                margin={{ left: 8, right: 24 }}
              >
                <CartesianGrid {...gridStyle} horizontal={false} vertical />
                <XAxis type="number" {...axisStyle} tickFormatter={(v: number) => formatINRCompact(v)} />
                <YAxis type="category" dataKey="symbol" width={90} {...axisStyle} />
                <Tooltip
                  {...tooltipStyle}
                  cursor={{ fill: "rgba(140,165,200,0.06)" }}
                  formatter={(v) => formatINRCompact(Number(v))}
                />
                <Bar dataKey="marketCap" name="Market Cap" radius={[0, 4, 4, 0]} barSize={16}>
                  {[...livePeers]
                    .sort((a, b) => (b.marketCap ?? 0) - (a.marketCap ?? 0))
                    .map((p) => (
                      <Cell key={p.symbol} fill={p.symbol === activeSymbol ? CHART_COLORS.amber : CHART_COLORS.slate} />
                    ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <Card className="glass-hover">
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle>Live Peer Quotes</CardTitle>
              <div className="flex items-center gap-2">
                {quarters && quarters.length > 0 && (
                  <Select value={quarter || quarters[0].value} onValueChange={setQuarter}>
                    <SelectTrigger className="h-7 w-32 text-xs">
                      <SelectValue placeholder="Quarter" />
                    </SelectTrigger>
                    <SelectContent>
                      {quarters.map((q) => (
                        <SelectItem key={q.value} value={q.value}>
                          {q.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                <Badge variant="bull" className="gap-1.5">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-bull opacity-60" />
                    <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-bull" />
                  </span>
                  NSE
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead className="text-right">LTP</TableHead>
                    <TableHead className="text-right">Chg %</TableHead>
                    <TableHead className="text-right">M.Cap</TableHead>
                    <TableHead className="text-right">P/E</TableHead>
                    <TableHead className="text-right">Promoter %</TableHead>
                    <TableHead className="text-right">D/E</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {livePeers.map((p) => (
                    <TableRow key={p.symbol} className={cn(p.symbol === activeSymbol && "bg-primary/8")}>
                      <TableCell>
                        <Link to={`/stocks/${p.symbol}`} className="hover:text-primary">
                          <span className={cn("font-mono text-xs font-semibold", p.symbol === activeSymbol && "text-primary")}>
                            {p.symbol}
                          </span>
                        </Link>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatMaybe(p.lastPrice)}</TableCell>
                      <TableCell
                        className={cn(
                          "text-right font-mono text-xs tabular",
                          p.pChange !== null && (p.pChange >= 0 ? "text-bull" : "text-bear"),
                        )}
                      >
                        {p.pChange !== null ? formatPercent(p.pChange) : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">
                        {p.marketCap !== null ? formatINRCompact(p.marketCap) : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatMaybe(p.pe, 1, "x")}</TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatMaybe(p.promoterHolding, 1, "%")}</TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatMaybe(p.debtToEquity)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Full peer table */}
      {!isError && data && (
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="mt-4">
          <Card className="glass-hover">
            <CardHeader>
              <CardTitle>Peer Comparison · {data.industry}</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Company</TableHead>
                    <TableHead className="text-right">Rev Growth</TableHead>
                    <TableHead className="text-right">Net Margin</TableHead>
                    <TableHead className="text-right">ROE</TableHead>
                    <TableHead className="text-right">ROCE</TableHead>
                    <TableHead className="text-right">D/E</TableHead>
                    <TableHead className="text-right">P/B</TableHead>
                    <TableHead className="text-right">Return</TableHead>
                    <TableHead className="text-right">Sharpe</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.peers.map((p) => (
                    <TableRow key={p.symbol} className={cn(p.symbol === data.symbol && "bg-primary/8")}>
                      <TableCell>
                        <Link to={`/stocks/${p.symbol}`} className="hover:text-primary">
                          <span className={cn("font-mono text-xs font-semibold", p.symbol === data.symbol && "text-primary")}>
                            {p.symbol}
                          </span>
                          <p className="max-w-[180px] truncate text-[11px] text-muted-foreground">{p.company}</p>
                        </Link>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatFraction(p.revenueGrowth)}</TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatFraction(p.netProfitMargin)}</TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatFraction(p.roe)}</TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatFraction(p.roce)}</TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatMaybe(p.debtToEquity)}</TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatMaybe(p.pbRatio, 1, "x")}</TableCell>
                      <TableCell
                        className={cn(
                          "text-right font-mono text-xs tabular",
                          p.cumulativeReturn !== null && (p.cumulativeReturn >= 0 ? "text-bull" : "text-bear"),
                        )}
                      >
                        {formatFraction(p.cumulativeReturn)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs tabular">{formatMaybe(p.sharpeRatio)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}

const PERCENT_METRICS = new Set([
  "revenue_growth", "earnings_growth", "net_profit_margin", "roe", "roce",
  "cumulative_return", "annualized_volatility",
]);

function formatMetricValue(metric: string, value: number | null): string {
  if (value === null) return "—";
  if (PERCENT_METRICS.has(metric)) return formatFraction(value);
  return formatMaybe(value);
}
