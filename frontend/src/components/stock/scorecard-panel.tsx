import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Gauge, HelpCircle, MinusCircle, XCircle } from "lucide-react";
import { apiClient } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { Scorecard } from "@/types";

const VERDICT = {
  good: { icon: CheckCircle2, cls: "text-bull" },
  average: { icon: MinusCircle, cls: "text-amber-500" },
  bad: { icon: XCircle, cls: "text-bear" },
  na: { icon: HelpCircle, cls: "text-muted-foreground/50" },
} as const;

function ratingTone(score: number | null): string {
  if (score === null) return "text-muted-foreground";
  if (score >= 75) return "text-bull";
  if (score >= 58) return "text-emerald-400";
  if (score >= 42) return "text-amber-500";
  return "text-bear";
}

export function ScorecardPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["scorecard", symbol],
    queryFn: async () => (await apiClient.get<Scorecard>(`/stocks/${symbol}/scorecard`)).data,
    staleTime: 10 * 60_000,
  });

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Gauge className="h-4 w-4 text-primary" /> Scorecard
        </CardTitle>
        {data && (
          <div className="flex items-center gap-2">
            <span className={cn("font-mono text-2xl font-bold tabular", ratingTone(data.overallScore))}>
              {data.overallScore ?? "—"}
            </span>
            <Badge variant="outline">{data.rating}</Badge>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="grid gap-2 sm:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : !data || data.checks.length === 0 ? (
          <p className="text-sm text-muted-foreground">No scorecard data yet for {symbol}.</p>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2">
            {data.checks.map((c) => {
              const v = VERDICT[c.verdict] ?? VERDICT.na;
              const Icon = v.icon;
              return (
                <motion.div
                  key={c.category}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-start gap-2 rounded-lg border border-border/60 bg-card/40 p-3"
                >
                  <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", v.cls)} />
                  <div className="min-w-0">
                    <span className="text-sm font-medium">{c.category}</span>
                    <p className="text-xs text-muted-foreground">{c.detail}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
