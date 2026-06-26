import { Fragment, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ChevronDown, Scale } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useStockValuation, useValuationLeaderboard } from "@/hooks/queries";
import { usePreferences } from "@/contexts/preferences";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

type Verdict = "undervalued" | "overvalued" | "all";

const VERDICT_BADGE: Record<string, { label: string; variant: "bull" | "bear" | "hold" }> = {
  undervalued: { label: "Undervalued", variant: "bull" },
  overvalued: { label: "Overvalued", variant: "bear" },
  "fairly valued": { label: "Fair", variant: "hold" },
};

function fmtNum(v: number | null | undefined, d = 1): string {
  return v == null ? "—" : v.toFixed(d);
}

/** Plain-language "why this upside" — fetched lazily when a row is expanded. */
function ValuationReason({ symbol }: { symbol: string }) {
  const { data: v, isLoading } = useStockValuation(symbol);
  if (isLoading) return <Skeleton className="h-14 w-full rounded-lg" />;
  if (!v || v.fairValue == null || v.price == null) {
    return <p className="text-xs text-muted-foreground">No valuation breakdown available for {symbol}.</p>;
  }
  const up = v.upsidePct ?? 0;
  const hasPe = v.pe != null && v.peFairValue != null;
  const hasPb = v.pb != null && v.pbFairValue != null;
  const capped = Math.abs(up) >= 199;

  const legParts: string[] = [];
  if (hasPe) legParts.push(`P/E ${fmtNum(v.pe)} vs sector ${fmtNum(v.sectorPe)}`);
  if (hasPb) legParts.push(`P/B ${fmtNum(v.pb, 2)} vs sector ${fmtNum(v.sectorPb, 2)}`);
  const legText = legParts.join(" and ") || "its sector multiples";

  let reason =
    up >= 0
      ? `Trades at ${legText} — cheaper than peers. Quality-adjusting those multiples lifts fair value to ${formatINR(v.fairValue)}, ${up.toFixed(0)}% above the ${formatINR(v.price)} price.`
      : `Trades at ${legText} — richer than peers. Fair value works out to ${formatINR(v.fairValue)}, ${Math.abs(up).toFixed(0)}% below the ${formatINR(v.price)} price.`;
  if (capped)
    reason += ` The estimate is pinned at the model's ±200% ceiling: each multiple's fair-to-price ratio is capped at 3× to stop scale-artifact blow-ups, so read this as "deeply mispriced / directional", not a precise target.`;
  if (hasPb && !hasPe) reason += ` Only the P/B leg is used (no usable earnings/P/E), which lowers confidence.`;
  if (hasPe && !hasPb) reason += ` Only the P/E leg is used (no usable book value).`;

  return (
    <div className="space-y-2">
      <p className="text-xs leading-relaxed text-muted-foreground">{reason}</p>
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-[11px] text-muted-foreground">
        {hasPe && <span>P/E <b className="text-foreground">{fmtNum(v.pe)}</b> · sector {fmtNum(v.sectorPe)} · fair {fmtNum(v.fairPe)}</span>}
        {hasPb && <span>P/B <b className="text-foreground">{fmtNum(v.pb, 2)}</b> · sector {fmtNum(v.sectorPb, 2)} · fair {fmtNum(v.fairPb, 2)}</span>}
        <span>Confidence <b className="capitalize text-foreground">{v.confidence}</b></span>
      </div>
    </div>
  );
}

export default function ValuationPage() {
  const [verdict, setVerdict] = useState<Verdict>("undervalued");
  const [openSym, setOpenSym] = useState<string | null>(null);
  const { prefs } = usePreferences();
  const { data, isLoading } = useValuationLeaderboard(verdict === "all" ? undefined : verdict, 60, prefs.universe);

  return (
    <div>
      <PageHeader
        title="Fair Value"
        description="Sector-relative, quality-adjusted fair value (P/E tilted by growth, P/B by ROE) versus the current price. A screening signal to surface mispricings — not a price target. Low-confidence and outlier estimates are excluded."
      />

      <div className="mt-4 flex gap-2">
        <Button size="sm" variant={verdict === "undervalued" ? "default" : "outline"} onClick={() => setVerdict("undervalued")}>
          Most undervalued
        </Button>
        <Button size="sm" variant={verdict === "overvalued" ? "default" : "outline"} onClick={() => setVerdict("overvalued")}>
          Most overvalued
        </Button>
        <Button size="sm" variant={verdict === "all" ? "default" : "outline"} onClick={() => setVerdict("all")}>
          All
        </Button>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-11 w-full" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">No stocks match this view.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Stock</th>
                  <th className="hidden p-3 sm:table-cell">Sector</th>
                  <th className="p-3 text-right">Price</th>
                  <th className="p-3 text-right">Fair Value</th>
                  <th className="p-3 text-right">Upside</th>
                  <th className="p-3 text-center">Verdict</th>
                  <th className="hidden p-3 text-center md:table-cell">Conf.</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => {
                  const v = VERDICT_BADGE[r.verdict ?? ""] ?? VERDICT_BADGE["fairly valued"];
                  const up = r.upsidePct ?? 0;
                  const open = openSym === r.symbol;
                  return (
                    <Fragment key={r.symbol}>
                      <motion.tr
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        onClick={() => setOpenSym(open ? null : r.symbol)}
                        title="Why this upside?"
                        className="cursor-pointer border-b border-border/40 hover:bg-muted/30"
                      >
                        <td className="p-3">
                          <Link
                            to={`/stocks/${r.symbol}`}
                            onClick={(e) => e.stopPropagation()}
                            className="font-mono font-medium hover:text-primary"
                          >
                            {r.symbol}
                          </Link>
                          <div className="max-w-[14rem] truncate text-xs text-muted-foreground">{r.name}</div>
                        </td>
                        <td className="hidden p-3 text-xs text-muted-foreground sm:table-cell">{r.sector ?? "—"}</td>
                        <td className="p-3 text-right font-mono tabular">{r.price != null ? formatINR(r.price) : "—"}</td>
                        <td className="p-3 text-right font-mono tabular">{r.fairValue != null ? formatINR(r.fairValue) : "—"}</td>
                        <td className="p-3 text-right">
                          <span className="inline-flex items-center justify-end gap-1">
                            <span className={cn("font-mono font-medium tabular", up >= 0 ? "text-bull" : "text-bear")}>
                              {up >= 0 ? "+" : ""}{up.toFixed(1)}%
                            </span>
                            <ChevronDown className={cn("h-3.5 w-3.5 text-muted-foreground transition-transform", open && "rotate-180")} />
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={v.variant}>{v.label}</Badge>
                        </td>
                        <td className="hidden p-3 text-center text-xs capitalize text-muted-foreground md:table-cell">
                          {r.confidence}
                        </td>
                      </motion.tr>
                      {open && (
                        <tr className="border-b border-border/40 bg-muted/10">
                          <td colSpan={7} className="px-3 pb-3">
                            <ValuationReason symbol={r.symbol} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Scale className="h-3.5 w-3.5" />
        Relative model only — assumes peers are fairly priced. Cross-check with the fundamentals and scorecard on each stock page.
      </p>
    </div>
  );
}
