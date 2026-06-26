import { motion } from "framer-motion";
import { Gauge } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketMood } from "@/hooks/queries";
import { cn } from "@/lib/utils";

function zoneTone(zone: string): string {
  if (zone.includes("Extreme Fear")) return "text-bear";
  if (zone === "Fear") return "text-amber-400";
  if (zone === "Neutral") return "text-muted-foreground";
  if (zone === "Greed") return "text-emerald-400";
  return "text-bull"; // Extreme Greed
}

export function MarketMood() {
  const { data, isLoading } = useMarketMood();

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
      <Card className="glass-hover">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-primary" /> Market Mood Index
          </CardTitle>
          {data && <span className="text-[10px] uppercase tracking-wide text-muted-foreground">{data.sample} stocks</span>}
        </CardHeader>
        <CardContent>
          {isLoading || !data ? (
            <Skeleton className="h-24 w-full rounded-lg" />
          ) : (
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              {/* headline */}
              <div className="shrink-0 sm:w-40">
                <div className={cn("font-mono text-4xl font-bold tabular", zoneTone(data.zone))}>
                  {Math.round(data.value)}
                </div>
                <div className={cn("text-sm font-semibold", zoneTone(data.zone))}>{data.zone}</div>
              </div>

              {/* fear → greed bar */}
              <div className="flex-1">
                <div className="relative h-2.5 w-full rounded-full bg-gradient-to-r from-bear via-amber-400 to-bull">
                  <div
                    className="absolute -top-1 h-4.5 w-1 -translate-x-1/2 rounded-full bg-foreground shadow"
                    style={{ left: `${data.value}%`, height: "1.1rem", top: "-0.2rem" }}
                  />
                </div>
                <div className="mt-1 flex justify-between text-[10px] text-muted-foreground/70">
                  <span>Extreme Fear</span><span>Neutral</span><span>Extreme Greed</span>
                </div>
                {/* components */}
                <div className="mt-3 grid grid-cols-3 gap-3">
                  {data.components.map((c) => (
                    <div key={c.label}>
                      <div className="flex justify-between text-[10px] text-muted-foreground">
                        <span className="truncate">{c.label}</span>
                        <span className="font-mono">{Math.round(c.value)}</span>
                      </div>
                      <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-muted/50">
                        <div
                          className={cn("h-full rounded-full", c.value >= 55 ? "bg-bull" : c.value >= 45 ? "bg-amber-400" : "bg-bear")}
                          style={{ width: `${c.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
