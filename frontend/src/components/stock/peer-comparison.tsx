import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { apiClient } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatFraction, formatINR, formatINRCompact } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { PeerComparison } from "@/types";

function num(v: number | null, digits = 1): string {
  return v == null ? "—" : v.toFixed(digits);
}

/** Tone a growth/return cell green/red by sign. */
function frac(v: number | null) {
  return (
    <span className={cn(v == null ? "text-muted-foreground" : v >= 0 ? "text-bull" : "text-bear")}>
      {formatFraction(v)}
    </span>
  );
}

export function PeerComparisonPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["peers", symbol],
    queryFn: async () => (await apiClient.get<PeerComparison>(`/stocks/${symbol}/peers`)).data,
    staleTime: 10 * 60_000,
  });

  const peers = data?.peers ?? [];

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Users className="h-4 w-4 text-primary" /> Peer Comparison
        </CardTitle>
        {data?.group && (
          <Badge variant="outline" className="font-normal">
            {data.group} · by {data.groupedBy}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-56 w-full rounded-lg" />
        ) : peers.length < 2 ? (
          <p className="text-sm text-muted-foreground">
            Not enough peers with comparable fundamentals for {symbol}.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-2.5">Stock</th>
                  <th className="p-2.5 text-right">Price</th>
                  <th className="p-2.5 text-right">M-Cap</th>
                  <th className="p-2.5 text-right">P/E</th>
                  <th className="p-2.5 text-right">P/B</th>
                  <th className="p-2.5 text-right">ROE</th>
                  <th className="hidden p-2.5 text-right sm:table-cell">NPM</th>
                  <th className="p-2.5 text-right">Rev ↑</th>
                </tr>
              </thead>
              <tbody>
                {peers.map((p) => (
                  <tr
                    key={p.symbol}
                    className={cn(
                      "border-b border-border/40",
                      p.isTarget ? "bg-primary/10" : "hover:bg-muted/30",
                    )}
                  >
                    <td className="p-2.5">
                      <Link
                        to={`/stocks/${p.symbol}`}
                        className={cn("font-mono font-medium hover:text-primary", p.isTarget && "text-primary")}
                      >
                        {p.symbol}
                      </Link>
                      <div className="max-w-[12rem] truncate text-xs text-muted-foreground">{p.name}</div>
                    </td>
                    <td className="p-2.5 text-right font-mono tabular">{p.price != null ? formatINR(p.price) : "—"}</td>
                    <td className="p-2.5 text-right font-mono tabular text-muted-foreground">
                      {p.marketCap != null ? formatINRCompact(p.marketCap) : "—"}
                    </td>
                    <td className="p-2.5 text-right font-mono tabular">{num(p.pe)}</td>
                    <td className="p-2.5 text-right font-mono tabular">{num(p.pb)}</td>
                    <td className="p-2.5 text-right font-mono tabular">{frac(p.roe)}</td>
                    <td className="hidden p-2.5 text-right font-mono tabular sm:table-cell">{frac(p.npm)}</td>
                    <td className="p-2.5 text-right font-mono tabular">{frac(p.revenueGrowth)}</td>
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
