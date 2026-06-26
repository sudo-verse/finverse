import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useStockTechnicals } from "@/hooks/queries";
import { formatINR, formatCompact } from "@/lib/format";
import { cn } from "@/lib/utils";

const TREND: Record<string, { label: string; variant: "bull" | "bear" | "hold" }> = {
  bullish: { label: "Bullish", variant: "bull" },
  bearish: { label: "Bearish", variant: "bear" },
  neutral: { label: "Neutral", variant: "hold" },
};

function MA({ label, value, price }: { label: string; value: number | null; price: number | null }) {
  const above = value != null && price != null && price >= value;
  return (
    <div className="rounded-lg border border-border/60 bg-card/40 p-2.5">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="font-mono text-sm font-medium">{value != null ? formatINR(value) : "—"}</div>
      {value != null && price != null && (
        <div className={cn("text-[10px] font-medium", above ? "text-bull" : "text-bear")}>
          {above ? "Price above" : "Price below"}
        </div>
      )}
    </div>
  );
}

export function TechnicalsPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useStockTechnicals(symbol);

  if (isLoading) {
    return (
      <Card className="mt-6">
        <CardHeader><CardTitle>Technicals</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-40 w-full rounded-lg" /></CardContent>
      </Card>
    );
  }
  if (!data || data.score == null) {
    return (
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary" /> Technicals
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Not enough price history to compute indicators for {symbol} yet ({data?.bars ?? 0} bars).
          </p>
        </CardContent>
      </Card>
    );
  }

  const trend = TREND[data.trend ?? "neutral"] ?? TREND.neutral;
  const rsi = data.rsi;
  const pivots: [string, number | null][] = [
    ["S2", data.s2], ["S1", data.s1], ["Pivot", data.pivot], ["R1", data.r1], ["R2", data.r2],
  ];

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" /> Technicals
        </CardTitle>
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm font-semibold">{Math.round(data.score)}/100</span>
          <Badge variant={trend.variant}>{trend.label}</Badge>
          {data.goldenCross != null && (
            <span className={cn("text-[10px] font-medium uppercase tracking-wide", data.goldenCross ? "text-bull" : "text-bear")}>
              {data.goldenCross ? "Golden cross" : "Death cross"}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* signal chips */}
        <div className="flex flex-wrap gap-1.5">
          {data.signals.map((s, i) => (
            <span
              key={i}
              className={cn(
                "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium",
                s.tone === "bull" && "border-bull/25 bg-bull/10 text-bull",
                s.tone === "bear" && "border-bear/25 bg-bear/10 text-bear",
                s.tone === "neutral" && "border-border/60 bg-muted/40 text-muted-foreground",
              )}
            >
              {s.label}{s.value ? ` · ${s.value}` : ""}
            </span>
          ))}
        </div>

        {/* moving averages */}
        <div className="grid grid-cols-3 gap-2">
          <MA label="20-DMA" value={data.sma20} price={data.price} />
          <MA label="50-DMA" value={data.sma50} price={data.price} />
          <MA label="200-DMA" value={data.sma200} price={data.price} />
        </div>

        {/* RSI + MACD */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-border/60 bg-card/40 p-3">
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="text-muted-foreground">RSI (14)</span>
              <span className="font-mono font-medium">{rsi != null ? rsi.toFixed(0) : "—"}</span>
            </div>
            {rsi != null && (
              <div className="relative h-1.5 w-full rounded-full bg-gradient-to-r from-bull/40 via-muted to-bear/40">
                <div className="absolute -top-0.5 h-2.5 w-0.5 bg-foreground" style={{ left: `${rsi}%` }} />
              </div>
            )}
            <div className="mt-1 flex justify-between text-[9px] text-muted-foreground/70">
              <span>Oversold 30</span><span>70 Overbought</span>
            </div>
          </div>
          <div className="rounded-lg border border-border/60 bg-card/40 p-3 text-xs">
            <div className="mb-1 text-muted-foreground">MACD (12,26,9)</div>
            <div className="flex justify-between font-mono"><span>MACD</span><span>{data.macd ?? "—"}</span></div>
            <div className="flex justify-between font-mono"><span>Signal</span><span>{data.macdSignal ?? "—"}</span></div>
            <div className="flex justify-between font-mono">
              <span>Histogram</span>
              <span className={cn((data.macdHist ?? 0) >= 0 ? "text-bull" : "text-bear")}>{data.macdHist ?? "—"}</span>
            </div>
          </div>
        </div>

        {/* pivots */}
        <div>
          <div className="mb-1.5 text-xs text-muted-foreground">Today's pivots (classic)</div>
          <div className="grid grid-cols-5 gap-1.5 text-center">
            {pivots.map(([k, v]) => (
              <div key={k} className={cn("rounded-md border border-border/60 bg-card/40 p-1.5",
                k === "Pivot" && "border-primary/40 bg-primary/10")}>
                <div className="text-[10px] text-muted-foreground">{k}</div>
                <div className="font-mono text-xs">{v != null ? formatINR(v) : "—"}</div>
              </div>
            ))}
          </div>
        </div>

        {/* volume */}
        {data.volLatest != null && data.volAvg20 != null && (
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Volume {formatCompact(data.volLatest)} vs 20-day avg {formatCompact(data.volAvg20)}</span>
            <span className={cn("font-medium", data.volLatest >= data.volAvg20 ? "text-bull" : "text-muted-foreground")}>
              {data.volAvg20 > 0 ? `${(data.volLatest / data.volAvg20).toFixed(1)}×` : "—"}
            </span>
          </div>
        )}

        <p className="text-[11px] text-muted-foreground">
          Indicators from {data.bars} daily bars. A trading-signal view, not advice.
        </p>
      </CardContent>
    </Card>
  );
}
