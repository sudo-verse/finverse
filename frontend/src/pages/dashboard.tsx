import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, ArrowDownRight, ArrowUpRight, Building2, Flame, Newspaper, Wallet } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { MarketsBoard } from "@/components/dashboard/markets-board";
import { MarketMood } from "@/components/dashboard/market-mood";
import { InstitutionalFlows } from "@/components/dashboard/institutional-flows";
import { SectorHeatmap } from "@/components/dashboard/sector-heatmap";
import { MetricCard, MetricCardSkeleton } from "@/components/shared/metric-card";
import { ChartCard, ChartSkeleton } from "@/components/shared/chart-card";
import { SentimentDot, SignalBadge } from "@/components/shared/signal-badge";
import { CHART_COLORS, SIGNAL_COLORS, axisStyle, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDashboard, useMarketMovers } from "@/hooks/queries";
import {
  formatCompact,
  formatFraction,
  formatINR,
  formatINRCompact,
  formatNumber,
  formatPercent,
  stripHtml,
  timeAgo,
} from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Mover, Sentiment, SignalType } from "@/types";

function MoverList({ movers }: { movers: Mover[] }) {
  if (movers.length === 0) {
    return <p className="py-6 text-center text-sm text-muted-foreground">No data right now.</p>;
  }
  return (
    <div className="space-y-1">
      {movers.slice(0, 6).map((m) => (
        <Link
          key={m.symbol}
          to={`/stocks/${m.symbol}`}
          className="flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-accent/50"
        >
          <span className="w-28 shrink-0 truncate font-mono text-xs font-semibold">{m.symbol}</span>
          <span className="flex-1 text-right font-mono text-xs tabular">
            {m.lastPrice !== null ? formatINR(m.lastPrice) : "—"}
          </span>
          <span className="w-20 shrink-0 text-right font-mono text-[11px] tabular text-muted-foreground">
            {m.tradedVolume !== null ? formatCompact(m.tradedVolume) : "—"}
          </span>
          <span
            className={cn(
              "w-16 shrink-0 text-right font-mono text-xs tabular",
              (m.pChange ?? 0) >= 0 ? "text-bull" : "text-bear",
            )}
          >
            {m.pChange !== null ? formatPercent(m.pChange) : "—"}
          </span>
        </Link>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();
  const { data: movers } = useMarketMovers();

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Market intelligence overview · NSE event engine"
        actions={
          <Badge variant="muted" className="normal-case tracking-normal">
            Last sync · {new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
          </Badge>
        }
      />

      {/* Top metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {isLoading || !data ? (
          Array.from({ length: 5 }).map((_, i) => <MetricCardSkeleton key={i} />)
        ) : (
          <>
            <MetricCard
              index={0}
              label="Total Companies"
              value={formatNumber(data.metrics.totalCompanies, 0)}
              icon={Building2}
              delta={`${formatNumber(data.metrics.priceRows, 0)} price rows`}
            />
            <MetricCard
              index={1}
              label="Total Signals"
              value={formatNumber(data.metrics.totalSignals, 0)}
              icon={Activity}
              delta={`${data.metrics.holdSignals} hold`}
            />
            <MetricCard
              index={2}
              label="Buy Signals"
              value={formatNumber(data.metrics.buySignals, 0)}
              icon={ArrowUpRight}
              accent="text-bull"
              deltaTone="up"
              delta={
                data.metrics.totalSignals
                  ? `${Math.round((data.metrics.buySignals / data.metrics.totalSignals) * 100)}% of total`
                  : undefined
              }
            />
            <MetricCard
              index={3}
              label="Sell Signals"
              value={formatNumber(data.metrics.sellSignals, 0)}
              icon={ArrowDownRight}
              accent="text-bear"
              deltaTone="down"
              delta={
                data.metrics.totalSignals
                  ? `${Math.round((data.metrics.sellSignals / data.metrics.totalSignals) * 100)}% of total`
                  : undefined
              }
            />
            <MetricCard
              index={4}
              label="Portfolio Value"
              value={data.metrics.portfolioValue !== null ? formatINRCompact(data.metrics.portfolioValue) : "—"}
              icon={Wallet}
              accent="text-chart-4"
              deltaTone={(data.metrics.portfolioDayChangePct ?? 0) >= 0 ? "up" : "down"}
              delta={
                data.metrics.portfolioValue === null
                  ? "no holdings yet"
                  : data.metrics.portfolioDayChangePct !== null
                    ? `${formatFraction(data.metrics.portfolioDayChangePct)} today`
                    : undefined
              }
            />
          </>
        )}
      </div>

      {/* Market Mood Index — fear ↔ greed */}
      <MarketMood />

      {/* Live markets: index chart, indices board, turnover */}
      <MarketsBoard />

      {/* Daily FII/DII cash-market flows */}
      <InstitutionalFlows />

      {/* Sector rotation heatmap */}
      <SectorHeatmap />

      {/* Charts row */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard title="Signal Distribution" description="Engine output split" delay={0.05}>
          {isLoading || !data ? (
            <ChartSkeleton height={240} />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={data.signalDistribution}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={62}
                  outerRadius={90}
                  paddingAngle={4}
                  strokeWidth={0}
                >
                  {data.signalDistribution.map((entry) => (
                    <Cell key={entry.name} fill={SIGNAL_COLORS[entry.name] ?? CHART_COLORS.slate} />
                  ))}
                </Pie>
                <Tooltip {...tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          )}
          {data && (
            <div className="mt-2 flex justify-center gap-5">
              {data.signalDistribution.map((d) => (
                <div key={d.name} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ background: SIGNAL_COLORS[d.name] ?? CHART_COLORS.slate }}
                  />
                  {d.name} · {d.value}
                </div>
              ))}
            </div>
          )}
        </ChartCard>

        <ChartCard title="Industry Distribution" description="Signals by industry" delay={0.1}>
          {isLoading || !data ? (
            <ChartSkeleton height={260} />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.industryDistribution} layout="vertical" margin={{ left: 8, right: 8 }}>
                <CartesianGrid {...gridStyle} horizontal={false} vertical />
                <XAxis type="number" {...axisStyle} allowDecimals={false} />
                <YAxis type="category" dataKey="industry" width={140} {...axisStyle} />
                <Tooltip {...tooltipStyle} cursor={{ fill: "rgba(140,165,200,0.06)" }} />
                <Bar dataKey="count" fill={CHART_COLORS.blue} radius={[0, 4, 4, 0]} barSize={14} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Daily Signal Trend" description="14-day signal flow" delay={0.15}>
          {isLoading || !data ? (
            <ChartSkeleton height={260} />
          ) : data.dailySignalTrend.length === 0 ? (
            <div className="flex h-[260px] items-center justify-center text-sm text-muted-foreground">
              No signals in the last 14 days
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={data.dailySignalTrend} margin={{ left: -16, right: 8 }}>
                <defs>
                  <linearGradient id="gBuy" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={CHART_COLORS.green} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={CHART_COLORS.green} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gHold" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={CHART_COLORS.amber} stopOpacity={0.25} />
                    <stop offset="100%" stopColor={CHART_COLORS.amber} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid {...gridStyle} />
                <XAxis dataKey="date" {...axisStyle} tickFormatter={(d: string) => d.slice(5)} />
                <YAxis {...axisStyle} allowDecimals={false} />
                <Tooltip {...tooltipStyle} />
                <Area type="monotone" dataKey="hold" stroke={CHART_COLORS.amber} strokeWidth={1.5} fill="url(#gHold)" />
                <Area type="monotone" dataKey="buy" stroke={CHART_COLORS.green} strokeWidth={2} fill="url(#gBuy)" />
                <Area type="monotone" dataKey="sell" stroke={CHART_COLORS.rose} strokeWidth={2} fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Live market movers (NSE) */}
      {movers && (
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18 }} className="mt-6">
          <Card className="glass-hover">
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="flex items-center gap-2">
                <Flame className="h-4 w-4 text-hold" /> Market Movers
              </CardTitle>
              <Badge variant="bull" className="gap-1.5">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-bull opacity-60" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-bull" />
                </span>
                NSE LIVE
              </Badge>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="gainers">
                <TabsList>
                  <TabsTrigger value="gainers">Top Gainers</TabsTrigger>
                  <TabsTrigger value="losers">Top Losers</TabsTrigger>
                  <TabsTrigger value="active">Most Active</TabsTrigger>
                </TabsList>
                <div className="flex items-center justify-end px-2 pt-2 text-[10px] uppercase tracking-wider text-muted-foreground/70">
                  <span className="w-28" />
                  <span className="flex-1 text-right">LTP</span>
                  <span className="w-20 text-right">Volume</span>
                  <span className="w-16 text-right">Chg %</span>
                </div>
                <TabsContent value="gainers" className="mt-1">
                  <MoverList movers={movers.gainers} />
                </TabsContent>
                <TabsContent value="losers" className="mt-1">
                  <MoverList movers={movers.losers} />
                </TabsContent>
                <TabsContent value="active" className="mt-1">
                  <MoverList movers={movers.mostActive} />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Activity feeds */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card className="glass-hover h-full">
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-primary" /> Latest Signals
              </CardTitle>
              <Link to="/signals" className="text-xs font-medium text-primary hover:underline">
                View all →
              </Link>
            </CardHeader>
            <CardContent className="space-y-1">
              {isLoading || !data
                ? Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)
                : data.recentSignals.map((s) => (
                    <Link
                      key={s.id}
                      to={s.symbol ? `/stocks/${s.symbol}` : "/signals"}
                      className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-accent/50"
                    >
                      <SignalBadge signal={s.signal as SignalType} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">{s.symbol ?? "—"}</p>
                        <p className="truncate text-xs text-muted-foreground">{stripHtml(s.eventTitle)}</p>
                      </div>
                      <div className="shrink-0 text-right">
                        <p className="font-mono text-xs tabular text-muted-foreground">
                          {s.confidence !== null ? `${Math.round(s.confidence * 100)}%` : "—"}
                        </p>
                        <p className="text-[10px] text-muted-foreground/70">
                          {s.timestamp ? timeAgo(s.timestamp) : ""}
                        </p>
                      </div>
                    </Link>
                  ))}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
          <Card className="glass-hover h-full">
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="flex items-center gap-2">
                <Newspaper className="h-4 w-4 text-chart-4" /> Latest News Events
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              {isLoading || !data
                ? Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)
                : data.recentNews.map((n) => (
                    <div
                      key={n.id}
                      className="flex items-start gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-accent/50"
                    >
                      <span className="mt-0.5 w-20 shrink-0 font-mono text-xs font-semibold text-primary">
                        {n.symbol ?? "—"}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="line-clamp-2 text-sm leading-snug">
                          {stripHtml(n.headline) || "(no headline)"}
                        </p>
                        <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                          {n.sentiment && <SentimentDot sentiment={n.sentiment as Sentiment} withLabel />}
                          <span>·</span>
                          <span>{n.source}</span>
                          <span>·</span>
                          <span>{n.timestamp ? timeAgo(n.timestamp) : ""}</span>
                        </div>
                      </div>
                    </div>
                  ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
