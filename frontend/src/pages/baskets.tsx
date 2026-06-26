import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Boxes, ChevronDown } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useBaskets, useBasket } from "@/hooks/queries";
import { cn } from "@/lib/utils";

function Ret({ v }: { v: number | null }) {
  if (v == null) return <span className="text-muted-foreground">—</span>;
  return <span className={cn("font-mono tabular", v >= 0 ? "text-bull" : "text-bear")}>{v >= 0 ? "+" : ""}{v.toFixed(1)}%</span>;
}

function BasketDetailRows({ basketKey }: { basketKey: string }) {
  const { data, isLoading } = useBasket(basketKey);
  if (isLoading) return <Skeleton className="h-24 w-full" />;
  if (!data) return null;
  return (
    <div className="mt-2 overflow-x-auto rounded-lg border border-border/40">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border/40 text-left text-[10px] uppercase tracking-wider text-muted-foreground">
            <th className="p-2">Stock</th>
            <th className="p-2 text-right">1M</th>
            <th className="p-2 text-right">3M</th>
            <th className="p-2 text-right">1Y</th>
          </tr>
        </thead>
        <tbody>
          {data.constituents.map((c) => (
            <tr key={c.symbol} className="border-b border-border/20 last:border-0 hover:bg-muted/20">
              <td className="p-2">
                <Link to={`/stocks/${c.symbol}`} className="font-mono font-medium hover:text-primary">{c.symbol}</Link>
              </td>
              <td className="p-2 text-right"><Ret v={c.ret1m} /></td>
              <td className="p-2 text-right"><Ret v={c.ret3m} /></td>
              <td className="p-2 text-right"><Ret v={c.ret1y} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function BasketsPage() {
  const { data, isLoading } = useBaskets();
  const [open, setOpen] = useState<string | null>(null);

  return (
    <div>
      <PageHeader
        title="Baskets"
        description="Curated thematic baskets — hand-picked groups of stocks with equal-weighted returns, computed from our own price history. Tap a basket to see its constituents."
      />

      {isLoading ? (
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-36 w-full rounded-xl" />)}
        </div>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {(data ?? []).map((b, i) => (
            <motion.div key={b.key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
              <Card className="glass-hover">
                <CardHeader className="cursor-pointer" onClick={() => setOpen(open === b.key ? null : b.key)}>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Boxes className="h-4 w-4 text-primary" /> {b.name}
                        <span className="text-xs font-normal text-muted-foreground">· {b.count} stocks</span>
                      </CardTitle>
                      <p className="mt-1 max-w-md text-xs text-muted-foreground">{b.thesis}</p>
                    </div>
                    <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted-foreground transition-transform", open === b.key && "rotate-180")} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-6 text-sm">
                    <div><div className="text-[10px] uppercase text-muted-foreground">1M</div><Ret v={b.ret1m} /></div>
                    <div><div className="text-[10px] uppercase text-muted-foreground">3M</div><Ret v={b.ret3m} /></div>
                    <div><div className="text-[10px] uppercase text-muted-foreground">1Y</div><Ret v={b.ret1y} /></div>
                    <div className="ml-auto text-right">
                      <div className="text-[10px] uppercase text-muted-foreground">Top 1M</div>
                      <div className="font-mono text-xs">{b.top.join(" · ") || "—"}</div>
                    </div>
                  </div>
                  <AnimatePresence>
                    {open === b.key && (
                      <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                        <BasketDetailRows basketKey={b.key} />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Boxes className="h-3.5 w-3.5" />
        Equal-weighted theme returns for research, not investable products or recommendations.
      </p>
    </div>
  );
}
