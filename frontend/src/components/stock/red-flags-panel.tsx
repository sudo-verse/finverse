import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useStockRedFlags } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import type { RedFlag } from "@/types";

const SEV_STYLE: Record<string, string> = {
  high: "border-bear/30 bg-bear/10 text-bear",
  medium: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  low: "border-border/60 bg-muted/40 text-muted-foreground",
  info: "border-bull/25 bg-bull/10 text-bull",
};

function FlagRow({ f }: { f: RedFlag }) {
  const Icon = f.severity === "info" ? CheckCircle2 : f.severity === "high" ? ShieldAlert : AlertTriangle;
  return (
    <div className={cn("flex items-start gap-2 rounded-lg border px-3 py-2 text-sm", SEV_STYLE[f.severity] ?? SEV_STYLE.low)}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <span className="font-medium">{f.label}</span>
        {f.detail && <span className="ml-1.5 text-xs opacity-80">· {f.detail}</span>}
      </div>
    </div>
  );
}

export function RedFlagsPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useStockRedFlags(symbol);

  if (isLoading) {
    return (
      <Card className="mt-6">
        <CardHeader><CardTitle>Red Flags</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-28 w-full rounded-lg" /></CardContent>
      </Card>
    );
  }
  if (!data) return null;

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-primary" /> Red Flags
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          {data.flags.map((f, i) => <FlagRow key={i} f={f} />)}
        </div>

        {/* quick stats */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat label="ASM/GSM" value={data.gsm ?? data.asm ?? "None"} tone={data.gsm || data.asm ? "bad" : "good"} />
          <Stat
            label="Promoter pledge"
            value={data.pledgedPct != null ? `${data.pledgedPct.toFixed(1)}%` : "—"}
            tone={data.pledgedPct != null && data.pledgedPct >= 15 ? "bad" : "neutral"}
          />
          <Stat
            label="Leverage"
            value={data.leverage != null ? `${(data.leverage * 100).toFixed(0)}%` : "—"}
            tone={data.stress === "high" ? "bad" : data.stress === "elevated" ? "warn" : "neutral"}
          />
          <Stat
            label="Promoter holding"
            value={data.promoterHoldingPct != null ? `${data.promoterHoldingPct.toFixed(1)}%` : "—"}
            tone="neutral"
          />
        </div>

        <p className="text-[11px] text-muted-foreground">
          Surveillance from NSE ASM/GSM lists; pledge from NSE disclosures; stress is a leverage proxy (omitted for
          lenders/insurers). Not advice.
        </p>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone: "good" | "bad" | "warn" | "neutral" }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/40 p-2.5">
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div
        className={cn(
          "truncate text-sm font-medium",
          tone === "bad" && "text-bear",
          tone === "warn" && "text-amber-400",
          tone === "good" && "text-bull",
        )}
      >
        {value}
      </div>
    </div>
  );
}
