import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BadgeCheck, PieChart as PieChartIcon, Scale } from "lucide-react";
import { getPerformance, getProfile, getShareholding } from "@/api/services";
import { ChartCard, ChartSkeleton } from "@/components/shared/chart-card";
import { PIE_PALETTE, axisStyle, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCorporateData } from "@/hooks/queries";
import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Shareholding pattern + performance-vs-index + exchange profile, all live NSE. */
export function NseInsights({ symbol }: { symbol: string }) {
  const shareholding = useCorporateData("shareholding", symbol, getShareholding, true);
  const performance = useCorporateData("performance", symbol, getPerformance, true);
  const profile = useCorporateData("profile", symbol, getProfile, true);

  // Pivot periods into chart rows: { date, [category]: pct } (oldest → newest)
  const categories = [
    ...new Set(shareholding.data?.flatMap((p) => p.holdings.map((h) => h.category)) ?? []),
  ];
  const shareRows = [...(shareholding.data ?? [])].reverse().map((p) => {
    const row: Record<string, string | number> = { date: p.date };
    for (const h of p.holdings) {
      if (h.pct !== null) row[h.category] = h.pct;
    }
    return row;
  });

  // Ownership change detection: latest quarter vs previous, per category.
  const [latest, previous] = shareholding.data ?? [];
  const ownershipChanges = (latest?.holdings ?? [])
    .map((h) => {
      const prev = previous?.holdings.find((p) => p.category === h.category);
      const delta = h.pct !== null && prev?.pct !== null && prev?.pct !== undefined ? h.pct - prev.pct : null;
      return { category: h.category, pct: h.pct, delta };
    })
    .sort((a, b) => Math.abs(b.delta ?? 0) - Math.abs(a.delta ?? 0));
  const promoterChange = ownershipChanges.find((c) => /promoter/i.test(c.category));

  return (
    <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
      {/* Shareholding pattern */}
      <ChartCard title="Shareholding Pattern" description="Quarterly disclosures · % of equity" delay={0.05}>
        {shareholding.isLoading ? (
          <ChartSkeleton height={240} />
        ) : shareholding.isError || shareRows.length === 0 ? (
          <p className="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
            Shareholding data unavailable
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={shareRows} margin={{ left: -16, right: 8 }}>
              <CartesianGrid {...gridStyle} />
              <XAxis dataKey="date" {...axisStyle} tickFormatter={(d: string) => d.slice(3)} />
              <YAxis {...axisStyle} domain={[0, 100]} tickFormatter={(v: number) => `${v}%`} />
              <Tooltip {...tooltipStyle} cursor={{ fill: "rgba(140,165,200,0.06)" }} formatter={(v) => `${v}%`} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {categories.map((c, i) => (
                <Bar key={c} dataKey={c} stackId="holding" fill={PIE_PALETTE[i % PIE_PALETTE.length]} barSize={28} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}

        {/* QoQ ownership changes (promoter move is the headline signal) */}
        {ownershipChanges.length > 0 && (
          <div className="mt-2 space-y-1.5">
            {promoterChange && promoterChange.delta !== null && (
              <div
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium",
                  promoterChange.delta > 0.01
                    ? "bg-bull/10 text-bull"
                    : promoterChange.delta < -0.01
                      ? "bg-bear/10 text-bear"
                      : "bg-secondary/40 text-muted-foreground",
                )}
              >
                {promoterChange.delta > 0.01
                  ? `▲ Promoter holding increased ${promoterChange.delta.toFixed(2)} pp QoQ`
                  : promoterChange.delta < -0.01
                    ? `▼ Promoter holding decreased ${Math.abs(promoterChange.delta).toFixed(2)} pp QoQ`
                    : "Promoter holding unchanged QoQ"}
              </div>
            )}
            <div className="flex flex-wrap gap-1.5">
              {ownershipChanges.map((c) => (
                <span
                  key={c.category}
                  className="flex items-center gap-1 rounded-md bg-secondary/40 px-2 py-1 text-[10px] text-muted-foreground"
                >
                  {c.category}
                  <span className="font-mono tabular text-foreground">{c.pct?.toFixed(2)}%</span>
                  {c.delta !== null && Math.abs(c.delta) > 0.005 && (
                    <span className={cn("font-mono tabular", c.delta > 0 ? "text-bull" : "text-bear")}>
                      {c.delta > 0 ? "+" : ""}
                      {c.delta.toFixed(2)}
                    </span>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}
      </ChartCard>

      {/* Performance vs index */}
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card className="glass-hover h-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Scale className="h-4 w-4 text-primary" /> Returns vs Index
            </CardTitle>
          </CardHeader>
          <CardContent>
            {performance.isLoading ? (
              <Skeleton className="h-56 w-full" />
            ) : performance.isError ? (
              <p className="py-10 text-center text-sm text-muted-foreground">Performance data unavailable</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Period</TableHead>
                    <TableHead className="text-right">{symbol}</TableHead>
                    <TableHead className="text-right">Index</TableHead>
                    <TableHead className="text-right">α</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {performance.data
                    ?.filter((r) => r.stock !== null)
                    .map((r) => {
                      const alpha = r.stock !== null && r.index !== null ? r.stock - r.index : null;
                      return (
                        <TableRow key={r.period}>
                          <TableCell className="font-mono text-xs font-semibold">{r.period}</TableCell>
                          <TableCell
                            className={cn(
                              "text-right font-mono text-xs tabular",
                              (r.stock ?? 0) >= 0 ? "text-bull" : "text-bear",
                            )}
                          >
                            {r.stock !== null ? formatPercent(r.stock) : "—"}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs tabular text-muted-foreground">
                            {r.index !== null ? formatPercent(r.index) : "—"}
                          </TableCell>
                          <TableCell
                            className={cn(
                              "text-right font-mono text-xs tabular",
                              alpha !== null && (alpha >= 0 ? "text-bull" : "text-bear"),
                            )}
                          >
                            {alpha !== null ? formatPercent(alpha, 1) : "—"}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Exchange profile */}
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <Card className="glass-hover h-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BadgeCheck className="h-4 w-4 text-bull" /> Exchange Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {profile.isLoading ? (
              <Skeleton className="h-56 w-full" />
            ) : profile.isError || !profile.data ? (
              <p className="py-10 text-center text-sm text-muted-foreground">Profile unavailable</p>
            ) : (
              <>
                <div className="flex flex-wrap gap-2">
                  {profile.data.isFno && <Badge variant="bull">F&O</Badge>}
                  {profile.data.isSlb && <Badge>SLB</Badge>}
                  {profile.data.isSuspended && <Badge variant="bear">Suspended</Badge>}
                  {profile.data.activeSeries.map((s) => (
                    <Badge key={s} variant="muted">
                      Series {s}
                    </Badge>
                  ))}
                </div>
                <div className="rounded-lg bg-secondary/40 px-3 py-2.5 text-xs">
                  <span className="text-muted-foreground">ISIN · </span>
                  <span className="font-mono">{profile.data.isin ?? "—"}</span>
                </div>
                {profile.data.about && (
                  <p className="line-clamp-4 text-xs leading-relaxed text-muted-foreground">{profile.data.about}</p>
                )}
                <div>
                  <p className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    <PieChartIcon className="h-3 w-3" /> Index memberships · {profile.data.indices.length}
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {profile.data.indices.slice(0, 8).map((idx) => (
                      <span key={idx} className="rounded-md bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                        {idx}
                      </span>
                    ))}
                    {profile.data.indices.length > 8 && (
                      <span
                        className="cursor-help rounded-md bg-muted px-2 py-0.5 text-[10px] text-primary"
                        title={profile.data.indices.slice(8).join("\n")}
                      >
                        +{profile.data.indices.length - 8} more
                      </span>
                    )}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
