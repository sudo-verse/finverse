import { Scale } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useStockValuation } from "@/hooks/queries";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

const VERDICT: Record<string, { label: string; variant: "bull" | "bear" | "hold" }> = {
  undervalued: { label: "Undervalued", variant: "bull" },
  overvalued: { label: "Overvalued", variant: "bear" },
  "fairly valued": { label: "Fairly valued", variant: "hold" },
};

function num(v: number | null | undefined, digits = 1): string {
  return v == null ? "—" : v.toFixed(digits);
}

export function ValuationPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useStockValuation(symbol);

  if (isLoading) {
    return (
      <Card className="mt-6">
        <CardHeader><CardTitle>Fair Value</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-40 w-full rounded-lg" /></CardContent>
      </Card>
    );
  }
  if (!data || data.fairValue == null || data.price == null) {
    return (
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Scale className="h-4 w-4 text-primary" /> Fair Value
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Not enough comparable multiples to estimate a fair value for {symbol}.
          </p>
        </CardContent>
      </Card>
    );
  }

  const verdict = VERDICT[data.verdict ?? ""] ?? VERDICT["fairly valued"];
  const up = data.upsidePct ?? 0;
  // Position the two markers on a shared scale (0 … max(price, fair) × 1.15).
  const scaleMax = Math.max(data.price, data.fairValue) * 1.15;
  const pricePos = (data.price / scaleMax) * 100;
  const fairPos = (data.fairValue / scaleMax) * 100;

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-primary" /> Fair Value
        </CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant={verdict.variant}>{verdict.label}</Badge>
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
            {data.confidence} confidence
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-end gap-x-8 gap-y-2">
          <div>
            <div className="text-xs text-muted-foreground">Estimated fair value</div>
            <div className="font-mono text-2xl font-semibold">{formatINR(data.fairValue)}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Current price</div>
            <div className="font-mono text-2xl font-semibold text-muted-foreground">{formatINR(data.price)}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Upside</div>
            <div className={cn("font-mono text-2xl font-semibold", up >= 0 ? "text-bull" : "text-bear")}>
              {up >= 0 ? "+" : ""}{up.toFixed(1)}%
            </div>
          </div>
        </div>

        {/* price vs fair-value scale */}
        <div className="relative h-9">
          <div className="absolute top-5 h-1.5 w-full rounded-full bg-muted" />
          <div
            className="absolute top-5 h-1.5 rounded-full bg-primary/40"
            style={{ left: `${Math.min(pricePos, fairPos)}%`, width: `${Math.abs(fairPos - pricePos)}%` }}
          />
          {/* fair-value marker */}
          <div className="absolute -translate-x-1/2" style={{ left: `${fairPos}%` }}>
            <div className="mx-auto h-3.5 w-3.5 rounded-full bg-primary ring-2 ring-background" />
            <div className="mt-0.5 whitespace-nowrap text-[10px] text-primary">Fair</div>
          </div>
          {/* price marker */}
          <div className="absolute top-3.5 -translate-x-1/2" style={{ left: `${pricePos}%` }}>
            <div className="mx-auto h-3.5 w-3.5 rounded-full bg-muted-foreground ring-2 ring-background" />
          </div>
        </div>

        {/* multiple legs */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-lg border border-border/60 bg-card/40 p-3">
            <div className="mb-1 text-xs font-medium text-muted-foreground">P/E leg (growth-adjusted)</div>
            <div className="font-mono text-xs">
              <div className="flex justify-between"><span>Current P/E</span><span>{num(data.pe)}</span></div>
              <div className="flex justify-between"><span>Fair P/E</span><span>{num(data.fairPe)}</span></div>
              <div className="flex justify-between text-muted-foreground"><span>Sector P/E</span><span>{num(data.sectorPe)}</span></div>
            </div>
          </div>
          <div className="rounded-lg border border-border/60 bg-card/40 p-3">
            <div className="mb-1 text-xs font-medium text-muted-foreground">P/B leg (ROE-adjusted)</div>
            <div className="font-mono text-xs">
              <div className="flex justify-between"><span>Current P/B</span><span>{num(data.pb, 2)}</span></div>
              <div className="flex justify-between"><span>Fair P/B</span><span>{num(data.fairPb, 2)}</span></div>
              <div className="flex justify-between text-muted-foreground"><span>Sector P/B</span><span>{num(data.sectorPb, 2)}</span></div>
            </div>
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          {data.method}. {data.note}
        </p>
      </CardContent>
    </Card>
  );
}
