import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, CheckCircle2, Gauge as GaugeIcon, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { SentimentGauge, ScoreBar, scoreColor, scoreLabel } from "@/components/sentiment/gauge";
import { CHART_COLORS, axisStyle, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { StockSearch } from "@/components/shared/stock-search";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useRecomputeSentiment, useSentiment, useSentimentHistory } from "@/hooks/queries";
import { formatFraction, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { PillarDetail, SentimentFactor } from "@/types";
import { useState } from "react";

const DEFAULT_SYMBOL = "TCS";
const TABS = ["Overall", "Technical", "Indicators", "Fundamental", "News"] as const;
type Tab = (typeof TABS)[number];

function statusTone(status: string): string {
  if (/bull|golden/.test(status)) return "text-bull";
  if (/bear|death|overbought/.test(status)) return "text-bear";
  return "text-hold";
}

function FactorCard({ f }: { f: SentimentFactor }) {
  return (
    <div className="rounded-xl border border-border/60 bg-secondary/30 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{f.name}</p>
        <span className={cn("text-[11px] font-bold uppercase", statusTone(f.status))}>{f.status}</span>
      </div>
      <div className="mt-1.5 flex items-center gap-3">
        <span className="font-mono text-xl font-bold tabular">{f.value !== null ? formatNumber(f.value, 2) : "—"}</span>
        {f.score !== null && (
          <span
            className="rounded-md px-1.5 py-0.5 font-mono text-[11px] font-semibold tabular"
            style={{ color: scoreColor(f.score), background: `color-mix(in srgb, ${scoreColor(f.score)} 12%, transparent)` }}
          >
            {Math.round(f.score)}
          </span>
        )}
      </div>
      {f.explanation && <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{f.explanation}</p>}
    </div>
  );
}

function PillarSection({ pillar }: { pillar: PillarDetail }) {
  return (
    <div className="space-y-4">
      <Card className="glass-hover">
        <CardContent className="flex flex-col items-center gap-4 py-6 sm:flex-row sm:gap-8">
          {pillar.score !== null ? (
            <SentimentGauge score={pillar.score} size={180} label={scoreLabel(pillar.score)} />
          ) : (
            <p className="text-sm text-muted-foreground">No data for this pillar</p>
          )}
          <p className="flex-1 text-sm leading-relaxed text-foreground/85">{pillar.summary}</p>
        </CardContent>
      </Card>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {pillar.factors.map((f) => (
          <FactorCard key={f.name} f={f} />
        ))}
      </div>
    </div>
  );
}

export default function SentimentPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const activeSymbol = (symbol ?? DEFAULT_SYMBOL).toUpperCase();
  const [tab, setTab] = useState<Tab>("Overall");
  const { data, isLoading, isError } = useSentiment(activeSymbol);
  const { data: history } = useSentimentHistory(activeSymbol);
  const recompute = useRecomputeSentiment();

  const pillar = (name: string) => data?.pillars.find((p) => p.name === name);

  return (
    <div>
      <PageHeader
        title="Sentiment Intelligence"
        description="Explainable BUY / SELL / HOLD scoring across technicals, fundamentals, news & ownership"
        actions={<StockSearch className="w-full sm:w-80" onSelect={(s) => navigate(`/sentiment/${s}`)} />}
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Badge variant="secondary" className="gap-1.5 font-mono text-sm normal-case">
          <GaugeIcon className="h-3.5 w-3.5" /> {activeSymbol}
        </Badge>
        <Tabs value={tab} onValueChange={(v) => setTab(v as Tab)}>
          <TabsList>
            {TABS.map((t) => (
              <TabsTrigger key={t} value={t}>
                {t}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <Button
          variant="outline"
          size="sm"
          className="ml-auto"
          disabled={recompute.isPending}
          onClick={() =>
            recompute.mutate(activeSymbol, { onError: () => toast.error("Recompute failed") })
          }
        >
          <RefreshCw className={cn("h-3.5 w-3.5", recompute.isPending && "animate-spin")} /> Recompute
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-64 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      ) : isError || !data ? (
        <Card className="py-16 text-center text-sm text-muted-foreground">
          Sentiment unavailable for {activeSymbol} — it needs price history in the database.
        </Card>
      ) : tab === "Overall" ? (
        <div className="space-y-4">
          {/* Gauge + breakdown */}
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="glass-hover h-full">
                <CardContent className="flex flex-col items-center justify-center gap-2 py-8">
                  <SentimentGauge
                    score={data.overall}
                    label={data.recommendation}
                    sublabel={`Confidence ${Math.round(data.confidence * 100)}%`}
                  />
                </CardContent>
              </Card>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="xl:col-span-2">
              <Card className="glass-hover h-full">
                <CardHeader>
                  <CardTitle>Sentiment Breakdown</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {data.pillars.map((p) => (
                    <ScoreBar key={p.name} name={p.name} score={p.score} />
                  ))}
                  <p className="pt-1 text-[10px] text-muted-foreground/70">
                    Weights: Technical 30% · Fundamental 30% · News 20% · Ownership 10% · Market 10% — renormalized over
                    pillars with data.
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Why: reasons & risks */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
            <Card className="glass-hover">
              <CardHeader>
                <CardTitle>Why {data.recommendation}?</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  {data.reasons.map((r) => (
                    <p key={r} className="flex items-start gap-2 text-xs leading-relaxed">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-bull" /> {r}
                    </p>
                  ))}
                  {data.reasons.length === 0 && <p className="text-xs text-muted-foreground">No bullish factors detected.</p>}
                </div>
                <div className="space-y-2">
                  {data.risks.map((r) => (
                    <p key={r} className="flex items-start gap-2 text-xs leading-relaxed">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-hold" /> {r}
                    </p>
                  ))}
                  {data.risks.length === 0 && <p className="text-xs text-muted-foreground">No major risk factors detected.</p>}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* AI analysis summary per pillar */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {data.pillars.map((p) => (
              <Card key={p.name} className="glass-hover">
                <CardContent className="py-4">
                  <p className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {p.name} Summary
                    <span className={cn("font-bold", statusTone(p.status))}>{p.status}</span>
                  </p>
                  <p className="mt-1.5 text-xs leading-relaxed text-foreground/85">{p.summary}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Sentiment history */}
          <Card className="glass-hover">
            <CardHeader>
              <CardTitle>Sentiment Score Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              {!history || history.length < 2 ? (
                <p className="py-6 text-center text-xs text-muted-foreground">
                  History builds up one snapshot per day — check back tomorrow to see the trend
                  {history?.[0]?.reason ? ` (latest move: ${history[0].reason})` : ""}.
                </p>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={history} margin={{ left: 4, right: 8 }}>
                    <defs>
                      <linearGradient id="gSent" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={CHART_COLORS.blue} stopOpacity={0.25} />
                        <stop offset="100%" stopColor={CHART_COLORS.blue} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid {...gridStyle} />
                    <XAxis dataKey="date" {...axisStyle} minTickGap={40} />
                    <YAxis {...axisStyle} domain={[0, 100]} width={36} />
                    <Tooltip
                      {...tooltipStyle}
                      formatter={(v, _n, item) => [
                        `${Math.round(Number(v))}${item?.payload?.reason ? ` — ${item.payload.reason}` : ""}`,
                        "Score",
                      ]}
                    />
                    <Area type="monotone" dataKey="overall" stroke={CHART_COLORS.blue} strokeWidth={2} fill="url(#gSent)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>
      ) : tab === "Technical" ? (
        <div className="space-y-4">
          {pillar("Technical") && <PillarSection pillar={pillar("Technical")!} />}
          {/* Momentum ranges */}
          <Card className="glass-hover">
            <CardHeader>
              <CardTitle>Price Momentum</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.momentum.map((m) => {
                const pos = m.high > m.low ? ((m.current - m.low) / (m.high - m.low)) * 100 : 50;
                return (
                  <div key={m.period} className="flex items-center gap-3">
                    <span className="w-8 shrink-0 font-mono text-xs font-semibold">{m.period}</span>
                    <span className="w-20 shrink-0 text-right font-mono text-[11px] tabular text-muted-foreground">
                      {formatNumber(m.low, 0)}
                    </span>
                    <div className="relative h-1.5 flex-1 rounded-full bg-gradient-to-r from-bear/50 via-hold/50 to-bull/50">
                      <span
                        className="absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background bg-foreground shadow"
                        style={{ left: `${pos}%` }}
                      />
                    </div>
                    <span className="w-20 shrink-0 font-mono text-[11px] tabular text-muted-foreground">
                      {formatNumber(m.high, 0)}
                    </span>
                    <span className={cn("w-16 shrink-0 text-right font-mono text-xs tabular", m.change >= 0 ? "text-bull" : "text-bear")}>
                      {formatFraction(m.change)}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      ) : tab === "Indicators" ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {/* Moving averages */}
          <Card className="glass-hover">
            <CardHeader>
              <CardTitle>Moving Averages</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(data.movingAverages).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between rounded-lg bg-secondary/40 px-3 py-2">
                    <span className="text-xs font-semibold uppercase text-muted-foreground">{k}</span>
                    <span className="font-mono text-sm tabular">{v !== null ? formatNumber(v, 1) : "—"}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          {/* Pivot levels */}
          <Card className="glass-hover">
            <CardHeader>
              <CardTitle>Pivot Levels</CardTitle>
            </CardHeader>
            <CardContent>
              {!data.pivots ? (
                <p className="py-6 text-center text-xs text-muted-foreground">Pivot levels unavailable.</p>
              ) : (
                <div className="space-y-1.5">
                  {([["R3", data.pivots.r3], ["R2", data.pivots.r2], ["R1", data.pivots.r1]] as const).map(([l, v]) => (
                    <div key={l} className="flex items-center justify-between rounded-lg bg-bear/8 px-3 py-1.5">
                      <span className="text-xs font-semibold text-bear">{l}</span>
                      <span className="font-mono text-sm tabular">{formatNumber(v, 1)}</span>
                    </div>
                  ))}
                  <div className="flex items-center justify-between rounded-lg bg-secondary/60 px-3 py-2">
                    <span className="text-xs font-bold">PIVOT</span>
                    <span className="font-mono text-sm font-bold tabular">{formatNumber(data.pivots.pivot, 1)}</span>
                  </div>
                  {([["S1", data.pivots.s1], ["S2", data.pivots.s2], ["S3", data.pivots.s3]] as const).map(([l, v]) => (
                    <div key={l} className="flex items-center justify-between rounded-lg bg-bull/8 px-3 py-1.5">
                      <span className="text-xs font-semibold text-bull">{l}</span>
                      <span className="font-mono text-sm tabular">{formatNumber(v, 1)}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : tab === "Fundamental" ? (
        pillar("Fundamental") && <PillarSection pillar={pillar("Fundamental")!} />
      ) : (
        <div className="space-y-4">
          {/* News split */}
          <Card className="glass-hover">
            <CardHeader>
              <CardTitle>News Sentiment Split</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex h-3 w-full overflow-hidden rounded-full">
                <div className="bg-bull" style={{ width: `${data.newsBucket.positivePct}%` }} />
                <div className="bg-muted" style={{ width: `${data.newsBucket.neutralPct}%` }} />
                <div className="bg-bear" style={{ width: `${data.newsBucket.negativePct}%` }} />
              </div>
              <div className="mt-2 flex flex-wrap gap-4 text-xs">
                <span className="text-bull">▲ Positive {data.newsBucket.positivePct}%</span>
                <span className="text-muted-foreground">— Neutral {data.newsBucket.neutralPct}%</span>
                <span className="text-bear">▼ Negative {data.newsBucket.negativePct}%</span>
                <span className="ml-auto text-muted-foreground">
                  {data.newsBucket.count} signals · impact {data.newsBucket.impact ?? "—"} (FinBERT, recency-weighted)
                </span>
              </div>
            </CardContent>
          </Card>
          {pillar("News") && <PillarSection pillar={pillar("News")!} />}
          {/* Ownership summary lives here too — it feeds the same narrative */}
          {pillar("Ownership") && <PillarSection pillar={pillar("Ownership")!} />}
        </div>
      )}
    </div>
  );
}
