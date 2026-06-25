import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, ShieldCheck, UserCheck } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useSastFeed } from "@/hooks/queries";
import { cn } from "@/lib/utils";

type Action = "all" | "acquisition" | "sale";

/** Share count → compact crore/lakh. */
function fmtShares(q: number | null): string {
  if (q == null) return "—";
  if (q >= 1e7) return `${(q / 1e7).toFixed(2)} Cr`;
  if (q >= 1e5) return `${(q / 1e5).toFixed(2)} L`;
  return q.toLocaleString("en-IN");
}

function isSale(action: string | null): boolean {
  const a = (action ?? "").toLowerCase();
  return a.startsWith("sale") || a.startsWith("dispos");
}

export default function InsiderPage() {
  const [action, setAction] = useState<Action>("all");
  const [promoter, setPromoter] = useState(false);
  const [search, setSearch] = useState("");
  const { data, isLoading } = useSastFeed({
    action: action === "all" ? undefined : action,
    promoter: promoter || undefined,
    days: 7,
    limit: 250,
  });

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return data ?? [];
    return (data ?? []).filter(
      (r) =>
        (r.company ?? "").toLowerCase().includes(q) ||
        (r.symbol ?? "").toLowerCase().includes(q) ||
        (r.acquirer ?? "").toLowerCase().includes(q),
    );
  }, [data, search]);

  return (
    <div>
      <PageHeader
        title="Insider & SAST Activity"
        description="Substantial acquisitions and sales (SEBI SAST Reg29) — acquirers and promoters crossing disclosure thresholds. The clearest 'skin in the game' signal: who is materially buying or selling, newest first."
      />

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-lg bg-muted/40 p-1">
          {(["all", "acquisition", "sale"] as Action[]).map((a) => (
            <button
              key={a}
              onClick={() => setAction(a)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors",
                action === a ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {a === "all" ? "All" : a === "acquisition" ? "Acquisitions" : "Sales"}
            </button>
          ))}
        </div>
        <Button size="sm" variant={promoter ? "default" : "outline"} onClick={() => setPromoter((p) => !p)}>
          <ShieldCheck className="mr-1.5 h-4 w-4" /> Promoters only
        </Button>
        <div className="relative ml-auto w-full max-w-xs sm:w-auto">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search company or acquirer…"
            className="w-full rounded-lg border border-border/60 bg-card/40 py-2 pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-primary/40"
          />
        </div>
      </div>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-11 w-full" />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            {data && data.length > 0
              ? "No filings match your filters."
              : "No SAST filings in the window — the NSE feed may be rate-limited; it refreshes shortly."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Stock</th>
                  <th className="p-3">Acquirer</th>
                  <th className="p-3 text-center">Action</th>
                  <th className="p-3 text-right">Shares</th>
                  <th className="p-3 text-right">% Traded</th>
                  <th className="hidden p-3 text-right md:table-cell">Holding After</th>
                  <th className="hidden p-3 text-right lg:table-cell">Date</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <motion.tr
                    key={`${r.symbol}-${r.acquirer}-${r.filedAt}-${i}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="border-b border-border/40 hover:bg-muted/30"
                  >
                    <td className="p-3">
                      <Link to={`/stocks/${r.symbol}`} className="font-mono font-medium hover:text-primary">
                        {r.symbol}
                      </Link>
                      <div className="max-w-[12rem] truncate text-xs text-muted-foreground">{r.company}</div>
                    </td>
                    <td className="p-3">
                      <span className="flex max-w-[16rem] items-center gap-1.5 truncate text-xs">
                        {r.isPromoter && <UserCheck className="h-3.5 w-3.5 shrink-0 text-primary" />}
                        {r.acquirer ?? "—"}
                      </span>
                      {r.isPromoter && <span className="text-[10px] uppercase tracking-wide text-primary/70">Promoter</span>}
                    </td>
                    <td className="p-3 text-center">
                      <Badge variant={isSale(r.action) ? "bear" : "bull"}>
                        {isSale(r.action) ? "SELL" : "BUY"}
                      </Badge>
                    </td>
                    <td className="p-3 text-right font-mono tabular text-muted-foreground">{fmtShares(r.shares)}</td>
                    <td className="p-3 text-right font-mono tabular">
                      {r.pctTraded != null ? `${r.pctTraded.toFixed(2)}%` : "—"}
                    </td>
                    <td className="hidden p-3 text-right font-mono tabular md:table-cell">
                      {r.pctAfter != null ? `${r.pctAfter.toFixed(2)}%` : "—"}
                    </td>
                    <td className="hidden p-3 text-right text-xs text-muted-foreground lg:table-cell">
                      {r.filedAt ?? r.tradeDate ?? "—"}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <ShieldCheck className="h-3.5 w-3.5" />
        SAST Reg29 covers acquirers crossing 5% (and 2% incremental) holding thresholds. Per-stock insider (PIT) trades appear on each stock page.
      </p>
    </div>
  );
}
