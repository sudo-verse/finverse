import { useState } from "react";
import { Check, CreditCard, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { startCheckout } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/auth";
import { cn } from "@/lib/utils";

const PLAN_RANK: Record<string, number> = { free: 0, pro: 1, scale: 2 };

const TIERS: { plan: "pro" | "scale"; name: string; price: string; api: string; blurb: string }[] = [
  { plan: "pro", name: "Pro", price: "$29/mo", api: "50,000 API req/day", blurb: "Production access for real apps." },
  { plan: "scale", name: "Scale", price: "$99/mo", api: "250,000 API req/day", blurb: "High-volume API for teams." },
];

/**
 * Plan & billing — shows the current plan and lets the user upgrade via Stripe
 * Checkout. After payment, Stripe redirects to /settings?billing=success, where
 * the API-keys card provisions a first key.
 */
export function PlanCard() {
  const { user } = useAuth();
  const [pending, setPending] = useState<string | null>(null);
  const current = user?.plan ?? "free";
  const rank = PLAN_RANK[current] ?? 0;

  const upgrade = async (plan: "pro" | "scale") => {
    setPending(plan);
    try {
      window.location.href = await startCheckout(plan);
    } catch (e) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail ?? "Could not start checkout. Please try again.");
      setPending(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-4 w-4 text-primary" /> Plan &amp; billing
        </CardTitle>
        <CardDescription>
          Your plan sets API rate limits and AI quotas. Cancel anytime.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Current plan</span>
          <Badge variant={current === "free" ? "secondary" : "default"} className="uppercase">
            {current}
          </Badge>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {TIERS.map((t) => {
            const isCurrent = current === t.plan;
            const isLower = (PLAN_RANK[t.plan] ?? 0) <= rank;
            return (
              <div
                key={t.plan}
                className={cn(
                  "flex flex-col rounded-lg border p-4",
                  isCurrent ? "border-primary/50 bg-primary/[0.05]" : "border-border/60",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">{t.name}</span>
                  <span className="text-sm font-bold">{t.price}</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{t.blurb}</p>
                <p className="mt-2 flex items-center gap-1.5 text-xs font-medium text-foreground/80">
                  <Check className="h-3.5 w-3.5 text-bull" /> {t.api}
                </p>
                <Button
                  size="sm"
                  variant={t.plan === "scale" ? "outline" : "default"}
                  className="mt-3"
                  disabled={isLower || pending !== null}
                  onClick={() => upgrade(t.plan)}
                >
                  {pending === t.plan ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  {isCurrent ? "Current plan" : isLower ? "Included" : `Upgrade to ${t.name}`}
                </Button>
              </div>
            );
          })}
        </div>
        <p className="text-xs text-muted-foreground">
          Need higher volume or an SLA?{" "}
          <a href="mailto:support@finverse.app?subject=Finverse%20API%20—%20Enterprise" className="text-primary hover:underline">
            Contact sales
          </a>
          .
        </p>
      </CardContent>
    </Card>
  );
}
