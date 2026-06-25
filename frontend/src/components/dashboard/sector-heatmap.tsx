import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Grid3x3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useSectors } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import type { SectorPerf } from "@/types";

type Period = "day" | "week" | "month" | "year";
const PERIODS: { key: Period; label: string }[] = [
  { key: "day", label: "Day" },
  { key: "week", label: "Week" },
  { key: "month", label: "Month" },
  { key: "year", label: "Year" },
];

/** Map a % change to a green/red tile background, intensity by magnitude. */
function tileStyle(v: number | null, max: number): { background: string; color: string } {
  if (v == null) return { background: "rgba(140,165,200,0.08)", color: "#8294ab" };
  const t = Math.min(Math.abs(v) / (max || 1), 1);
  const alpha = 0.12 + t * 0.45;
  const rgb = v >= 0 ? "16,185,129" : "244,63,94";
  return { background: `rgba(${rgb},${alpha})`, color: "#e6edf7" };
}

export function SectorHeatmap() {
  const [period, setPeriod] = useState<Period>("day");
  const { data, isLoading } = useSectors();

  const sorted = useMemo(() => {
    const rows = [...(data ?? [])];
    rows.sort((a, b) => (b[period] ?? -999) - (a[period] ?? -999));
    return rows;
  }, [data, period]);

  const max = useMemo(
    () => Math.max(0.5, ...sorted.map((s) => Math.abs(s[period] ?? 0))),
    [sorted, period],
  );

  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }} className="mt-6">
      <Card className="glass-hover">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <Grid3x3 className="h-4 w-4 text-primary" /> Sector Heatmap
          </CardTitle>
          <div className="flex gap-1 rounded-lg bg-muted/40 p-1">
            {PERIODS.map((p) => (
              <button
                key={p.key}
                onClick={() => setPeriod(p.key)}
                className={cn(
                  "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                  period === p.key ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {Array.from({ length: 12 }).map((_, i) => (
                <Skeleton key={i} className="h-20 rounded-lg" />
              ))}
            </div>
          ) : sorted.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Sector data unavailable right now.</p>
          ) : (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              {sorted.map((s: SectorPerf) => {
                const v = s[period];
                const st = tileStyle(v, max);
                return (
                  <div
                    key={s.index}
                    className="flex flex-col justify-between rounded-lg p-3 transition-transform hover:scale-[1.02]"
                    style={{ background: st.background }}
                    title={s.index}
                  >
                    <span className="text-sm font-semibold" style={{ color: st.color }}>
                      {s.name}
                    </span>
                    <span className="mt-1 font-mono text-lg font-bold tabular" style={{ color: st.color }}>
                      {v == null ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
