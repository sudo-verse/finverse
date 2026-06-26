import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
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
import { Activity, Briefcase, IndianRupee, Plus, Trash2, TrendingUp, Wallet } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { MetricCard, MetricCardSkeleton } from "@/components/shared/metric-card";
import { ChartCard, ChartSkeleton } from "@/components/shared/chart-card";
import { StockSearch } from "@/components/shared/stock-search";
import { CHART_COLORS, PIE_PALETTE, axisStyle, gridStyle, tooltipStyle } from "@/components/shared/chart-theme";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAddHolding, useClearHoldings, usePortfolio } from "@/hooks/queries";
import { formatCompact, formatFraction, formatINR, formatINRCompact, formatMaybe } from "@/lib/format";
import { cn } from "@/lib/utils";

function AddHoldingDialog() {
  const [open, setOpen] = useState(false);
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("10");
  const [avgPrice, setAvgPrice] = useState("");
  const addHolding = useAddHolding();

  const submit = () => {
    const qty = Number(quantity);
    if (!symbol || !qty || qty <= 0) {
      toast.error("Pick a symbol and a positive quantity");
      return;
    }
    addHolding.mutate(
      { symbol, quantity: qty, avgPrice: avgPrice ? Number(avgPrice) : null },
      {
        onSuccess: () => {
          toast.success(`Added ${qty} × ${symbol}`);
          setOpen(false);
          setSymbol("");
          setAvgPrice("");
        },
        onError: () => toast.error("Failed to add holding"),
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus /> Add holding
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>Add holding</DialogTitle>
        <DialogDescription>
          Positions are stored in the backend; quantities accumulate and average price is blended on repeat buys.
        </DialogDescription>
        <div className="space-y-4 pt-2">
          <div className="space-y-2">
            <Label>Stock</Label>
            {symbol ? (
              <div className="flex items-center justify-between rounded-md border border-input bg-secondary/40 px-3 py-2">
                <span className="font-mono text-sm font-semibold text-primary">{symbol}</span>
                <button
                  type="button"
                  className="cursor-pointer text-xs text-muted-foreground hover:text-foreground"
                  onClick={() => setSymbol("")}
                >
                  change
                </button>
              </div>
            ) : (
              <StockSearch onSelect={setSymbol} placeholder="Search NSE stocks…" />
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="qty">Quantity</Label>
              <Input id="qty" type="number" min="1" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="avg">Avg buy price (optional)</Label>
              <Input
                id="avg"
                type="number"
                min="0"
                placeholder="e.g. 2900"
                value={avgPrice}
                onChange={(e) => setAvgPrice(e.target.value)}
              />
            </div>
          </div>
          <Button className="w-full" onClick={submit} disabled={addHolding.isPending}>
            {addHolding.isPending ? "Adding…" : "Add to portfolio"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function PortfolioPage() {
  const { data, isLoading, isError } = usePortfolio();
  const clearHoldings = useClearHoldings();

  const allocation =
    data?.holdings
      .filter((h) => h.value !== null)
      .map((h) => ({ name: h.symbol, value: Math.round(h.value!) })) ?? [];

  const isEmpty = isError; // 404 → no holdings yet

  return (
    <div>
      <PageHeader
        title="Portfolio"
        description="Holdings, allocation and risk-adjusted performance"
        actions={
          <div className="flex items-center gap-2">
            {data && (
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  clearHoldings.mutate(undefined, {
                    onSuccess: () => toast.warning("Portfolio cleared"),
                  })
                }
              >
                <Trash2 /> Clear
              </Button>
            )}
            <AddHoldingDialog />
          </div>
        }
      />

      {/* Empty state */}
      {isEmpty && (
        <Card className="flex flex-col items-center justify-center gap-4 py-20 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Wallet className="h-7 w-7" />
          </div>
          <div>
            <p className="text-sm font-semibold">No holdings yet</p>
            <p className="mt-1 max-w-sm text-xs text-muted-foreground">
              Add your first position to unlock portfolio analytics — value, P&L, allocation, concentration and
              risk-adjusted returns, computed by the Finverse engine.
            </p>
          </div>
          <AddHoldingDialog />
        </Card>
      )}

      {!isEmpty && (
        <>
          {/* Summary metrics */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {isLoading || !data ? (
              Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)
            ) : (
              <>
                <MetricCard
                  index={0}
                  label="Total Value"
                  value={formatINRCompact(data.summary.totalValue)}
                  icon={Briefcase}
                  delta={
                    data.summary.totalCost !== null ? `Invested ${formatINRCompact(data.summary.totalCost)}` : undefined
                  }
                />
                <MetricCard
                  index={1}
                  label="Daily P&L"
                  value={data.summary.dayPnl !== null ? formatINRCompact(data.summary.dayPnl) : "—"}
                  icon={IndianRupee}
                  accent={(data.summary.dayPnl ?? 0) >= 0 ? "text-bull" : "text-bear"}
                  deltaTone={(data.summary.dayPnl ?? 0) >= 0 ? "up" : "down"}
                  delta={data.summary.dayPnlPct !== null ? formatFraction(data.summary.dayPnlPct, 2) : undefined}
                />
                <MetricCard
                  index={2}
                  label="Total Return"
                  value={data.summary.totalPnl !== null ? formatINRCompact(data.summary.totalPnl) : "—"}
                  icon={TrendingUp}
                  accent={(data.summary.totalPnl ?? 0) >= 0 ? "text-bull" : "text-bear"}
                  deltaTone={(data.summary.totalPnl ?? 0) >= 0 ? "up" : "down"}
                  delta={data.summary.totalPnlPct !== null ? formatFraction(data.summary.totalPnlPct, 1) : undefined}
                />
                <MetricCard
                  index={3}
                  label="Sharpe Ratio"
                  value={formatMaybe(data.summary.sharpeRatio)}
                  icon={Activity}
                  accent="text-chart-4"
                  delta={
                    data.summary.annualizedVolatility !== null
                      ? `vol ${formatFraction(data.summary.annualizedVolatility)} · ${data.summary.numHoldings} holdings`
                      : undefined
                  }
                />
              </>
            )}
          </div>

          {/* Charts */}
          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <ChartCard title="Allocation" description="By holding value" delay={0.05}>
              {isLoading || !data ? (
                <ChartSkeleton height={240} />
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={allocation}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={58}
                        outerRadius={85}
                        paddingAngle={3}
                        strokeWidth={0}
                      >
                        {allocation.map((_, i) => (
                          <Cell key={i} fill={PIE_PALETTE[i % PIE_PALETTE.length]} />
                        ))}
                      </Pie>
                      <Tooltip {...tooltipStyle} formatter={(v) => formatINRCompact(Number(v))} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="mt-1 flex flex-wrap justify-center gap-x-4 gap-y-1">
                    {allocation.map((a, i) => (
                      <span key={a.name} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                        <span className="h-2 w-2 rounded-full" style={{ background: PIE_PALETTE[i % PIE_PALETTE.length] }} />
                        {a.name}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </ChartCard>

            <ChartCard title="Sector Distribution" description="Exposure by industry" delay={0.1}>
              {isLoading || !data ? (
                <ChartSkeleton height={260} />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart
                    data={data.sectorAllocation.map((s) => ({ ...s, pct: s.weight * 100 }))}
                    layout="vertical"
                    margin={{ left: 8, right: 8 }}
                  >
                    <CartesianGrid {...gridStyle} horizontal={false} vertical />
                    <XAxis type="number" {...axisStyle} tickFormatter={(v: number) => `${v}%`} />
                    <YAxis type="category" dataKey="sector" width={130} {...axisStyle} />
                    <Tooltip
                      {...tooltipStyle}
                      cursor={{ fill: "rgba(140,165,200,0.06)" }}
                      formatter={(v) => `${Number(v).toFixed(1)}%`}
                    />
                    <Bar dataKey="pct" name="Weight" fill={CHART_COLORS.violet} radius={[0, 4, 4, 0]} barSize={14} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Portfolio Growth" description="Current holdings marked to market · 6 months" delay={0.15}>
              {isLoading || !data ? (
                <ChartSkeleton height={260} />
              ) : data.growth.length === 0 ? (
                <div className="flex h-[260px] items-center justify-center text-sm text-muted-foreground">
                  Not enough price history
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={data.growth} margin={{ left: -4, right: 8 }}>
                    <defs>
                      <linearGradient id="gPortfolio" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={CHART_COLORS.green} stopOpacity={0.3} />
                        <stop offset="100%" stopColor={CHART_COLORS.green} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid {...gridStyle} />
                    <XAxis dataKey="date" {...axisStyle} minTickGap={40} tickFormatter={(d: string) => d.slice(5)} />
                    <YAxis {...axisStyle} width={50} tickFormatter={(v: number) => formatCompact(v)} domain={["auto", "auto"]} />
                    <Tooltip {...tooltipStyle} formatter={(v) => formatINRCompact(Number(v))} />
                    <Area type="monotone" dataKey="value" name="Value" stroke={CHART_COLORS.green} strokeWidth={2} fill="url(#gPortfolio)" />
                    <Area
                      type="monotone"
                      dataKey="invested"
                      name="Invested"
                      stroke={CHART_COLORS.slate}
                      strokeWidth={1.5}
                      strokeDasharray="4 3"
                      fill="transparent"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
          </div>

          {/* Portfolio X-ray */}
          {data && (
            <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
              {/* Market-cap split */}
              <Card className="glass-hover">
                <CardHeader><CardTitle className="text-sm">Market-cap mix</CardTitle></CardHeader>
                <CardContent className="space-y-2.5">
                  {data.marketCapAllocation.length === 0 ? (
                    <p className="text-xs text-muted-foreground">Market-cap data unavailable.</p>
                  ) : (
                    data.marketCapAllocation.map((m) => (
                      <div key={m.bucket} className="text-xs">
                        <div className="mb-1 flex justify-between">
                          <span className="text-muted-foreground">{m.bucket}</span>
                          <span className="font-mono font-medium">{(m.weight * 100).toFixed(1)}%</span>
                        </div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/50">
                          <div
                            className={cn(
                              "h-full rounded-full",
                              m.bucket === "Large cap" && "bg-blue-500",
                              m.bucket === "Mid cap" && "bg-violet-500",
                              m.bucket === "Small cap" && "bg-amber-500",
                              m.bucket === "Unknown" && "bg-slate-500",
                            )}
                            style={{ width: `${m.weight * 100}%` }}
                          />
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Diversification */}
              <Card className="glass-hover">
                <CardHeader><CardTitle className="text-sm">Diversification</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {(() => {
                    const eff = data.summary.effectiveHoldings;
                    const grade = eff == null ? "—" : eff >= 8 ? "Excellent" : eff >= 5 ? "Good" : eff >= 3 ? "Moderate" : "Concentrated";
                    const tone = eff == null ? "text-muted-foreground" : eff >= 5 ? "text-bull" : eff >= 3 ? "text-hold" : "text-bear";
                    return (
                      <>
                        <div className="flex items-baseline justify-between">
                          <span className="text-xs text-muted-foreground">Diversification</span>
                          <span className={cn("text-sm font-semibold", tone)}>{grade}</span>
                        </div>
                        <div className="flex items-baseline justify-between text-xs">
                          <span className="text-muted-foreground">Effective holdings</span>
                          <span className="font-mono">{eff != null ? eff.toFixed(1) : "—"} <span className="text-muted-foreground/60">/ {data.summary.numHoldings}</span></span>
                        </div>
                        <div className="flex items-baseline justify-between text-xs">
                          <span className="text-muted-foreground">Top holding weight</span>
                          <span className="font-mono">{data.summary.topConcentration != null ? `${(data.summary.topConcentration * 100).toFixed(1)}%` : "—"}</span>
                        </div>
                        <div className="flex items-baseline justify-between text-xs">
                          <span className="text-muted-foreground">Sectors</span>
                          <span className="font-mono">{data.summary.numSectors}</span>
                        </div>
                      </>
                    );
                  })()}
                </CardContent>
              </Card>

              {/* Top movers (by total P&L) */}
              <Card className="glass-hover">
                <CardHeader><CardTitle className="text-sm">Best & worst</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {(() => {
                    const ranked = [...data.holdings].filter((h) => h.pnlPct != null).sort((a, b) => (b.pnlPct ?? 0) - (a.pnlPct ?? 0));
                    if (ranked.length === 0) return <p className="text-xs text-muted-foreground">No P&L data yet.</p>;
                    const best = ranked[0], worst = ranked[ranked.length - 1];
                    const Row = ({ h, label }: { h: typeof best; label: string }) => (
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
                          <Link to={`/stocks/${h.symbol}`} className="font-mono text-sm font-medium hover:text-primary">{h.symbol}</Link>
                        </div>
                        <span className={cn("font-mono text-sm font-semibold", (h.pnlPct ?? 0) >= 0 ? "text-bull" : "text-bear")}>
                          {(h.pnlPct ?? 0) >= 0 ? "+" : ""}{((h.pnlPct ?? 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                    );
                    return (
                      <>
                        <Row h={best} label="Best performer" />
                        <Row h={worst} label="Worst performer" />
                      </>
                    );
                  })()}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Holdings table */}
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mt-6">
            <Card className="glass-hover">
              <CardHeader>
                <CardTitle>Holdings</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading || !data ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Stock</TableHead>
                        <TableHead className="text-right">Qty</TableHead>
                        <TableHead className="text-right">Avg Price</TableHead>
                        <TableHead className="text-right">Current Price</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                        <TableHead className="text-right">Weight</TableHead>
                        <TableHead className="text-right">Day %</TableHead>
                        <TableHead className="text-right">Gain / Loss</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.holdings.map((h) => (
                        <TableRow key={h.symbol}>
                          <TableCell>
                            <Link to={`/stocks/${h.symbol}`} className="group">
                              <span className="font-mono text-sm font-semibold group-hover:text-primary">{h.symbol}</span>
                              <p className="text-xs text-muted-foreground">{h.industry ?? "—"}</p>
                            </Link>
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm tabular">{h.quantity}</TableCell>
                          <TableCell className="text-right font-mono text-sm tabular">
                            {h.avgPrice !== null ? formatINR(h.avgPrice) : "—"}
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm tabular">
                            {h.price !== null ? formatINR(h.price) : "—"}
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm tabular">
                            {h.value !== null ? formatINRCompact(h.value) : "—"}
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm tabular">{formatFraction(h.weight)}</TableCell>
                          <TableCell
                            className={cn(
                              "text-right font-mono text-sm tabular",
                              h.dayChangePct !== null && (h.dayChangePct >= 0 ? "text-bull" : "text-bear"),
                            )}
                          >
                            {formatFraction(h.dayChangePct, 2)}
                          </TableCell>
                          <TableCell
                            className={cn(
                              "text-right font-mono text-sm tabular",
                              h.pnl !== null && (h.pnl >= 0 ? "text-bull" : "text-bear"),
                            )}
                          >
                            {h.pnl !== null ? `${formatINRCompact(h.pnl)} (${formatFraction(h.pnlPct, 1)})` : "—"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </>
      )}
    </div>
  );
}
