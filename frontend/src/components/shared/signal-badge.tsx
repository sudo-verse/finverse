import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Sentiment, SignalType } from "@/types";
import { cn } from "@/lib/utils";

export function SignalBadge({ signal, className }: { signal: SignalType; className?: string }) {
  const variant = signal === "BUY" ? "bull" : signal === "SELL" ? "bear" : "hold";
  const Icon = signal === "BUY" ? ArrowUpRight : signal === "SELL" ? ArrowDownRight : Minus;
  return (
    <Badge variant={variant} className={className}>
      <Icon className="h-3 w-3" />
      {signal}
    </Badge>
  );
}

export function SentimentDot({ sentiment, withLabel = false }: { sentiment: Sentiment; withLabel?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs capitalize text-muted-foreground">
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          sentiment === "positive" && "bg-bull",
          sentiment === "negative" && "bg-bear",
          sentiment === "neutral" && "bg-hold",
        )}
      />
      {withLabel && sentiment}
    </span>
  );
}
