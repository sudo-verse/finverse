import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowLeft, CheckCircle2, Gauge as GaugeIcon, LineChart } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { SentimentGauge, ScoreBar, scoreColor } from "@/components/sentiment/gauge";
import { StockSearch } from "@/components/shared/stock-search";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useStockConviction } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import type { ConvictionPillar } from "@/types";

const DEFAULT_SYMBOL = "TCS";

const VERDICT: Record<string, { label: string; variant: "bull" | "bear" | "hold" }> = {
  "high conviction": { label: "High conviction", variant: "bull" },
  constructive: { label: "Constructive", variant: "bull" },
  neutral: { label: "Neutral", variant: "hold" },
  weak: { label: "Weak", variant: "bear" },
};

function PillarCard({ p }: { p: ConvictionPillar }) {
  return (
    <div className="rounded-xl border border-border/60 bg-secondary/30 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{p.label}</p>
        {p.score !== null && (
          <span
            className="rounded-md px-1.5 py-0.5 font-mono text-[11px] font-semibold tabular"
            style={{ color: scoreColor(p.score), background: `color-mix(in srgb, ${scoreColor(p.score)} 12%, transparent)` }}
          >
            {Math.round(p.score)}
          </span>
        )}
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
        {p.score !== null && (
          <div className="h-full rounded-full" style={{ width: `${p.score}%`, background: scoreColor(p.score) }} />
        )}
      </div>
      {p.detail && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{p.detail}</p>}
    </div>
  );
}

export default function SentimentDetailPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const sym = (symbol ?? DEFAULT_SYMBOL).toUpperCase();
  const navigate = useNavigate();
  const { data, isLoading } = useStockConviction(sym);

  const verdict = data ? VERDICT[data.verdict] ?? VERDICT.neutral : null;
  const strengths = data?.pillars.filter((p) => p.signal === "up") ?? [];
  const watchouts = data?.pillars.filter((p) => p.signal === "down") ?? [];

  return (
    <div>
      <PageHeader
        title="Sentiment Intelligence"
        description="Composite 0–100 read fusing valuation, momentum, smart money, insider/SAST, 52-week trend and news & mood."
        actions={<StockSearch className="w-full sm:w-80" onSelect={(s) => navigate(`/sentiment/${s}`)} />}
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Link to="/sentiment" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3.5 w-3.5" /> All stocks
        </Link>
        <Badge variant="secondary" className="gap-1.5 font-mono text-sm normal-case">
          <GaugeIcon className="h-3.5 w-3.5" /> {sym}
        </Badge>
        <Link to={`/stocks/${sym}`} className="ml-auto inline-flex items-center gap-1 text-xs text-primary hover:underline">
          <LineChart className="h-3.5 w-3.5" /> Full analysis
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-64 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      ) : !data ? (
        <Card className="py-16 text-center text-sm text-muted-foreground">
          Not enough signal coverage to score {sym} yet — at least three pillars are required.
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Gauge + breakdown */}
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="glass-hover h-full">
                <CardContent className="flex flex-col items-center justify-center gap-2 py-8">
                  <SentimentGauge
                    score={data.score}
                    label={verdict?.label}
                    sublabel={`${data.coverage} signal pillar${data.coverage === 1 ? "" : "s"}`}
                  />
                </CardContent>
              </Card>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="xl:col-span-2">
              <Card className="glass-hover h-full">
                <CardHeader><CardTitle>Score Breakdown</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {data.pillars.map((p) => <ScoreBar key={p.key} name={p.label} score={p.score} />)}
                  <p className="pt-1 text-[10px] text-muted-foreground/70">
                    Weights: Valuation 24% · Earnings momentum 20% · Smart money 20% · Insider/SAST 14% · 52-week trend
                    12% · News & mood 10% — renormalised over pillars with data.
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Why */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
            <Card className="glass-hover">
              <CardHeader><CardTitle>Why {verdict?.label}?</CardTitle></CardHeader>
              <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  {strengths.map((p) => (
                    <p key={p.key} className="flex items-start gap-2 text-xs leading-relaxed">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-bull" />
                      <span><b>{p.label}:</b> {p.detail}</span>
                    </p>
                  ))}
                  {strengths.length === 0 && <p className="text-xs text-muted-foreground">No standout strengths.</p>}
                </div>
                <div className="space-y-2">
                  {watchouts.map((p) => (
                    <p key={p.key} className="flex items-start gap-2 text-xs leading-relaxed">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-bear" />
                      <span><b>{p.label}:</b> {p.detail}</span>
                    </p>
                  ))}
                  {watchouts.length === 0 && <p className="text-xs text-muted-foreground">No major watch-outs.</p>}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Pillar cards */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {data.pillars.map((p) => <PillarCard key={p.key} p={p} />)}
          </div>

          <p className={cn("text-[11px] text-muted-foreground")}>A screening synthesis from Finverse signals, not advice.</p>
        </div>
      )}
    </div>
  );
}
