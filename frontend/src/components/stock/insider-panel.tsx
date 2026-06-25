import { UserCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useStockInsider } from "@/hooks/queries";
import { formatINRCompact } from "@/lib/format";

function fmtQty(q: number | null): string {
  if (q == null) return "—";
  if (q >= 1e7) return `${(q / 1e7).toFixed(2)} Cr`;
  if (q >= 1e5) return `${(q / 1e5).toFixed(2)} L`;
  return q.toLocaleString("en-IN");
}

export function InsiderPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useStockInsider(symbol, 20);
  const trades = data ?? [];

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserCheck className="h-4 w-4 text-primary" /> Insider Trades
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-48 w-full rounded-lg" />
        ) : trades.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent SEBI PIT insider disclosures for {symbol}.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-2.5">Person</th>
                  <th className="hidden p-2.5 sm:table-cell">Category</th>
                  <th className="p-2.5 text-right">Qty</th>
                  <th className="p-2.5 text-right">Value</th>
                  <th className="hidden p-2.5 text-right md:table-cell">Holding %</th>
                  <th className="hidden p-2.5 text-right lg:table-cell">Date</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t, i) => (
                  <tr key={`${t.person}-${t.filedAt}-${i}`} className="border-b border-border/40 hover:bg-muted/30">
                    <td className="p-2.5">
                      <span className="block max-w-[14rem] truncate">{t.person ?? "—"}</span>
                    </td>
                    <td className="hidden p-2.5 text-xs text-muted-foreground sm:table-cell">
                      {t.personCategory ?? "—"}
                    </td>
                    <td className="p-2.5 text-right font-mono tabular text-muted-foreground">{fmtQty(t.quantity)}</td>
                    <td className="p-2.5 text-right font-mono tabular">
                      {t.value != null ? formatINRCompact(t.value) : "—"}
                    </td>
                    <td className="hidden p-2.5 text-right font-mono tabular md:table-cell">
                      {t.pctBefore != null && t.pctAfter != null ? (
                        <span className={t.pctAfter > t.pctBefore ? "text-bull" : t.pctAfter < t.pctBefore ? "text-bear" : ""}>
                          {t.pctBefore.toFixed(2)} → {t.pctAfter.toFixed(2)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="hidden p-2.5 text-right text-xs text-muted-foreground lg:table-cell">
                      {t.filedAt ?? t.tradeDate ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
