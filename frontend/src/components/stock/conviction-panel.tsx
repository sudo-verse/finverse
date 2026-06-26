import { Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useStockConviction } from "@/hooks/queries";
import { cn } from "@/lib/utils";

const VERDICT: Record<string, { label: string; variant: "bull" | "bear" | "hold" }> = {
  "high conviction": { label: "High conviction", variant: "bull" },
  constructive: { label: "Constructive", variant: "bull" },
  neutral: { label: "Neutral", variant: "hold" },
  weak: { label: "Weak", variant: "bear" },
};

function tone(score: number): string {
  if (score >= 68) return "text-bull";
  if (score >= 56) return "text-emerald-400";
  if (score >= 44) return "text-muted-foreground";
  return "text-bear";
}
function barColor(signal: string): string {
  if (signal === "up") return "bg-bull";
  if (signal === "down") return "bg-bear";
  return "bg-slate-400";
}

export function ConvictionPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useStockConviction(symbol);

  if (isLoading) {
    return (
      <Card className="mt-6">
        <CardHeader><CardTitle>Conviction Score</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-40 w-full rounded-lg" /></CardContent>
      </Card>
    );
  }
  if (!data) {
    return (
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-4 w-4 text-primary" /> Conviction Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Not enough signal coverage to score {symbol} yet — at least three pillars are required.
          </p>
        </CardContent>
      </Card>
    );
  }

  const verdict = VERDICT[data.verdict] ?? VERDICT.neutral;

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Target className="h-4 w-4 text-primary" /> Conviction Score
        </CardTitle>
        <Badge variant={verdict.variant}>{verdict.label}</Badge>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Headline gauge */}
        <div className="flex items-center gap-5">
          <div className="shrink-0">
            <span className={cn("font-mono text-4xl font-bold tabular", tone(data.score))}>
              {Math.round(data.score)}
            </span>
            <span className="text-lg text-muted-foreground">/100</span>
          </div>
          <div className="flex-1">
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted/50">
              <div
                className={cn("h-full rounded-full", data.score >= 56 ? "bg-bull" : data.score >= 44 ? "bg-slate-400" : "bg-bear")}
                style={{ width: `${data.score}%` }}
              />
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">
              Weighted blend of {data.coverage} signal pillar{data.coverage === 1 ? "" : "s"}.
            </p>
          </div>
        </div>

        {/* Per-pillar breakdown */}
        <div className="space-y-2.5">
          {data.pillars.map((p) => (
            <div key={p.key} className="flex items-center gap-3 text-sm">
              <span className="w-32 shrink-0 text-xs text-muted-foreground">{p.label}</span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted/50">
                <div className={cn("h-full rounded-full", barColor(p.signal))} style={{ width: `${p.score ?? 0}%` }} />
              </div>
              <span className="w-10 shrink-0 text-right font-mono text-xs tabular text-muted-foreground">
                {p.score == null ? "—" : Math.round(p.score)}
              </span>
              <span className="hidden w-44 shrink-0 truncate text-right text-[11px] text-muted-foreground/80 sm:inline">
                {p.detail}
              </span>
            </div>
          ))}
        </div>

        <p className="text-xs text-muted-foreground">
          Fuses valuation, earnings momentum, smart-money flow, insider/SAST direction, 52-week trend and sentiment.
          A screening synthesis, not advice.
        </p>
      </CardContent>
    </Card>
  );
}
