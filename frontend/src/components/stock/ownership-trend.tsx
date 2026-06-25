import { useQuery } from "@tanstack/react-query";
import { Landmark } from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiClient } from "@/api/client";
import { axisStyle, CHART_COLORS, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { OwnershipHistoryRow } from "@/types";

/** Holder classes we trend, with display label + line colour. */
const SERIES: { key: keyof OwnershipHistoryRow; label: string; color: string }[] = [
  { key: "promoter", label: "Promoter", color: CHART_COLORS.violet },
  { key: "fii", label: "FII / FPI", color: CHART_COLORS.blue },
  { key: "dii", label: "DII", color: CHART_COLORS.green },
  { key: "mf", label: "Mutual Funds", color: CHART_COLORS.amber },
  { key: "insurance", label: "Insurance", color: CHART_COLORS.cyan },
];

function shortQuarter(period: string | null): string {
  // "31-Mar-2026" → "Mar'26"
  if (!period) return "";
  const [, mon, yr] = period.split("-");
  return yr ? `${mon}'${yr.slice(-2)}` : period;
}

export function OwnershipTrendPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["ownership-history", symbol],
    queryFn: async () =>
      (await apiClient.get<OwnershipHistoryRow[]>(`/ownership/${symbol}/history`, {
        params: { limit: 8 },
      })).data,
    staleTime: 30 * 60_000,
  });

  const rows = data ?? [];
  const chart = rows.map((r) => ({ ...r, q: shortQuarter(r.period) }));
  // only plot series that have at least one non-null point
  const active = SERIES.filter((s) => rows.some((r) => r[s.key] != null));
  const hasInstitutional = rows.some((r) => r.fii != null || r.dii != null);

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Landmark className="h-4 w-4 text-primary" /> Ownership Trend
          <span className="text-xs font-normal text-muted-foreground">· quarterly holding %</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-64 w-full rounded-lg" />
        ) : chart.length < 2 ? (
          <p className="text-sm text-muted-foreground">
            Not enough shareholding history yet for {symbol}.
          </p>
        ) : (
          <>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chart} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
                  <CartesianGrid {...gridStyle} />
                  <XAxis dataKey="q" {...axisStyle} />
                  <YAxis {...axisStyle} width={40} tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    {...tooltipStyle}
                    formatter={(v, name) => [`${Number(v).toFixed(2)}%`, name]}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {active.map((s) => (
                    <Line
                      key={s.key}
                      type="monotone"
                      dataKey={s.key}
                      name={s.label}
                      stroke={s.color}
                      strokeWidth={2}
                      dot={false}
                      connectNulls
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
            {!hasInstitutional && (
              <p className="mt-2 text-xs text-muted-foreground">
                FII/DII split not yet ingested for {symbol} — showing promoter trend only.
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
