import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Bell, BellPlus, Gauge as GaugeIcon, Star, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { scoreColor } from "@/components/sentiment/gauge";
import { StockSearch } from "@/components/shared/stock-search";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAlertRuleMutations, useAlertRules, useWatchlist, useWatchMutations } from "@/hooks/queries";
import { formatINR, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { AlertKind } from "@/types";

const ALERT_KINDS: { value: AlertKind; label: string; needsThreshold: boolean; hint: string }[] = [
  { value: "price_above", label: "Price above", needsThreshold: true, hint: "₹ level" },
  { value: "price_below", label: "Price below", needsThreshold: true, hint: "₹ level" },
  { value: "sentiment_above", label: "Sentiment above", needsThreshold: true, hint: "score 0–100" },
  { value: "sentiment_below", label: "Sentiment below", needsThreshold: true, hint: "score 0–100" },
  { value: "promoter_change", label: "Promoter holding change", needsThreshold: true, hint: "pp QoQ (e.g. 0.5)" },
  { value: "buy_signal", label: "Engine BUY signal", needsThreshold: false, hint: "" },
  { value: "near_52w_high", label: "Near 52-week high", needsThreshold: false, hint: "within % (default 2)" },
  { value: "near_52w_low", label: "Near 52-week low", needsThreshold: false, hint: "within % (default 2)" },
];

function AlertDialog({ symbol, onClose }: { symbol: string | null; onClose: () => void }) {
  const [kind, setKind] = useState<AlertKind>("price_above");
  const [threshold, setThreshold] = useState("");
  const { data: rules } = useAlertRules(symbol ?? undefined);
  const { create, remove } = useAlertRuleMutations();
  const def = ALERT_KINDS.find((k) => k.value === kind)!;

  const submit = () => {
    if (def.needsThreshold && !threshold.trim()) {
      toast.error("This alert needs a threshold");
      return;
    }
    create.mutate(
      { symbol: symbol!, kind, threshold: def.needsThreshold ? Number(threshold) : null },
      {
        onSuccess: () => {
          toast.success("Alert created — checked every 5 minutes");
          setThreshold("");
        },
        onError: () => toast.error("Could not create alert"),
      },
    );
  };

  return (
    <Dialog open={symbol !== null} onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <DialogTitle className="flex items-center gap-2 text-base">
          <Bell className="h-4 w-4 text-primary" /> Alerts — {symbol}
        </DialogTitle>
        <DialogDescription className="text-xs">
          Fires once per condition per 24h, in-app and on Telegram.
        </DialogDescription>
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Select value={kind} onValueChange={(v) => setKind(v as AlertKind)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ALERT_KINDS.map((k) => (
                  <SelectItem key={k.value} value={k.value}>
                    {k.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {def.needsThreshold && (
            <Input
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              placeholder={def.hint}
              type="number"
              className="w-32"
            />
          )}
          <Button onClick={submit} disabled={create.isPending}>
            Add
          </Button>
        </div>
        <div className="space-y-1.5">
          {(rules ?? []).map((r) => (
            <div key={r.id} className="flex items-center gap-2 rounded-lg bg-secondary/40 px-3 py-2 text-xs">
              <span className="font-medium">{ALERT_KINDS.find((k) => k.value === r.kind)?.label ?? r.kind}</span>
              {r.threshold !== null && <span className="font-mono tabular text-muted-foreground">{r.threshold}</span>}
              {r.lastTriggeredAt && <span className="text-[10px] text-muted-foreground">last fired recently</span>}
              <button
                type="button"
                aria-label="Delete alert"
                className="ml-auto cursor-pointer text-muted-foreground hover:text-bear"
                onClick={() => remove.mutate(r.id)}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
          {rules && rules.length === 0 && (
            <p className="py-2 text-center text-xs text-muted-foreground">No alerts for {symbol} yet.</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function WatchlistPage() {
  const { data, isLoading } = useWatchlist();
  const { add, remove } = useWatchMutations();
  const [alertSymbol, setAlertSymbol] = useState<string | null>(null);

  return (
    <div>
      <PageHeader
        title="Watchlist"
        description="Tracked stocks with live quotes, sentiment and alerts"
        actions={
          <StockSearch
            className="w-full sm:w-80"
            placeholder="Add a stock to track…"
            onSelect={(symbol) =>
              add.mutate(
                { symbol },
                {
                  onSuccess: () => toast.success(`${symbol} added to watchlist`),
                  onError: () => toast.error(`Could not add ${symbol}`),
                },
              )
            }
          />
        }
      />

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="overflow-hidden">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
          ) : !data || data.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <Star className="h-10 w-10 text-muted-foreground/40" />
              <p className="text-sm font-medium">Your watchlist is empty</p>
              <p className="max-w-sm text-xs text-muted-foreground">
                Search a stock above to start tracking it — you'll get live quotes, daily sentiment snapshots, and can
                set price / sentiment / promoter alerts.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Stock</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Change</TableHead>
                  <TableHead className="text-right">Sentiment</TableHead>
                  <TableHead className="text-right">Alerts</TableHead>
                  <TableHead className="w-24" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((w) => (
                  <TableRow key={w.symbol}>
                    <TableCell>
                      <Link to={`/stocks/${w.symbol}`} className="group">
                        <span className="font-mono text-sm font-semibold text-primary group-hover:underline">
                          {w.symbol}
                        </span>
                        <span className="block max-w-56 truncate text-xs text-muted-foreground">{w.name}</span>
                      </Link>
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm tabular">
                      {w.price !== null ? formatINR(w.price) : "—"}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right font-mono text-sm tabular",
                        (w.changePct ?? 0) >= 0 ? "text-bull" : "text-bear",
                      )}
                    >
                      {w.changePct !== null ? formatPercent(w.changePct) : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      {w.sentiment !== null ? (
                        <Link
                          to={`/sentiment/${w.symbol}`}
                          className="inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 font-mono text-xs font-semibold tabular"
                          style={{
                            color: scoreColor(w.sentiment),
                            background: `color-mix(in srgb, ${scoreColor(w.sentiment)} 12%, transparent)`,
                          }}
                          title={w.recommendation ?? undefined}
                        >
                          <GaugeIcon className="h-3 w-3" /> {Math.round(w.sentiment)}
                        </Link>
                      ) : (
                        <Link to={`/sentiment/${w.symbol}`} className="text-xs text-muted-foreground hover:underline">
                          compute →
                        </Link>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs tabular text-muted-foreground">
                      {w.alertCount > 0 ? w.alertCount : "—"}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" aria-label="Manage alerts" onClick={() => setAlertSymbol(w.symbol)}>
                          <BellPlus className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Remove from watchlist"
                          onClick={() =>
                            remove.mutate(w.symbol, { onSuccess: () => toast.success(`${w.symbol} removed`) })
                          }
                        >
                          <Trash2 className="h-4 w-4 text-muted-foreground" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </motion.div>

      <AlertDialog symbol={alertSymbol} onClose={() => setAlertSymbol(null)} />
    </div>
  );
}
