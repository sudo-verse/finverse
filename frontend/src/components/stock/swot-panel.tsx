import { Grid2x2, RefreshCw, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSwot, useRefreshSwot } from "@/hooks/queries";
import { cn } from "@/lib/utils";

const QUADRANTS = [
  { key: "strengths" as const, label: "Strengths", tone: "border-bull/25 bg-bull/5", dot: "bg-bull" },
  { key: "weaknesses" as const, label: "Weaknesses", tone: "border-bear/25 bg-bear/5", dot: "bg-bear" },
  { key: "opportunities" as const, label: "Opportunities", tone: "border-blue-500/25 bg-blue-500/5", dot: "bg-blue-400" },
  { key: "threats" as const, label: "Threats", tone: "border-amber-500/25 bg-amber-500/5", dot: "bg-amber-400" },
];

export function SwotPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useSwot(symbol);
  const refresh = useRefreshSwot();
  const has = Boolean(
    data && (data.strengths.length || data.weaknesses.length || data.opportunities.length || data.threats.length),
  );

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Grid2x2 className="h-4 w-4 text-primary" /> SWOT Analysis
        </CardTitle>
        <Button size="sm" variant="outline" disabled={refresh.isPending} onClick={() => refresh.mutate(symbol)}>
          {refresh.isPending ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
          {has ? "Regenerate" : "Generate"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading || refresh.isPending ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-lg" />)}
          </div>
        ) : !has ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Click <span className="font-medium text-foreground">Generate</span> to build an AI SWOT from {symbol}'s
            fundamentals, metrics and signals.
          </p>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {QUADRANTS.map((q) => (
                <div key={q.key} className={cn("rounded-lg border p-3", q.tone)}>
                  <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide">
                    <span className={cn("h-2 w-2 rounded-full", q.dot)} /> {q.label}
                  </div>
                  <ul className="space-y-1">
                    {(data![q.key] ?? []).map((point, i) => (
                      <li key={i} className="text-sm text-muted-foreground">• {point}</li>
                    ))}
                    {(data![q.key] ?? []).length === 0 && <li className="text-xs text-muted-foreground/60">—</li>}
                  </ul>
                </div>
              ))}
            </div>
            {data?.generatedAt && (
              <p className="mt-2 text-[10px] text-muted-foreground/70">
                AI-generated{data.model ? ` · ${data.model}` : ""} · grounded in Finverse data. Not advice.
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
