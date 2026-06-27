import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  delta?: string;
  deltaTone?: "up" | "down" | "neutral";
  accent?: string; // tailwind text-* class for the icon
  index?: number;
}

export function MetricCard({ label, value, icon: Icon, delta, deltaTone = "neutral", accent, index = 0 }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.06 }}
    >
      <Card className="glass-hover p-5">
        <div className="flex items-start justify-between">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
            <p className="mt-2 truncate font-mono text-2xl font-bold tabular">{value}</p>
            {delta && (
              <p
                className={cn(
                  "mt-1 font-mono text-xs tabular",
                  deltaTone === "up" && "text-bull",
                  deltaTone === "down" && "text-bear",
                  deltaTone === "neutral" && "text-muted-foreground",
                )}
              >
                {delta}
              </p>
            )}
          </div>
          <div className={cn("rounded-md bg-white/[0.04] p-2 ring-1 ring-white/[0.06]", accent ?? "text-primary")}>
            <Icon className="h-[18px] w-[18px]" />
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

export function MetricCardSkeleton() {
  return (
    <Card className="p-5">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-3 h-7 w-32" />
      <Skeleton className="mt-2 h-3 w-16" />
    </Card>
  );
}
