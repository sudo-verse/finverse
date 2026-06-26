import { useMemo, useState, useEffect } from "react";
import { Calculator } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDcf } from "@/hooks/queries";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Equity-FCF DCF, mirrored from the backend so sliders recompute instantly. */
function intrinsic(fcf: number, growth: number, terminal: number, discount: number, years: number, shares: number): number | null {
  if (shares <= 0 || discount <= terminal) return null;
  let pv = 0, f = fcf;
  for (let t = 1; t <= years; t++) {
    f *= 1 + growth;
    pv += f / (1 + discount) ** t;
  }
  const tv = (f * (1 + terminal)) / (discount - terminal);
  pv += tv / (1 + discount) ** years;
  return pv / shares;
}

function Slider({ label, value, min, max, step, suffix, onChange }: {
  label: string; value: number; min: number; max: number; step: number; suffix: string; onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-mono font-medium">{value}{suffix}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-muted accent-primary" />
    </div>
  );
}

export function DcfPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useDcf(symbol);

  const base = data?.scenarios.find((s) => s.name === "base");
  const [growth, setGrowth] = useState(10);
  const [discount, setDiscount] = useState(12);
  const [terminal, setTerminal] = useState(4);
  const [years, setYears] = useState(10);

  useEffect(() => {
    if (base) {
      setGrowth(Math.round(base.growth * 100));
      setDiscount(Math.round(base.discount * 100));
      setTerminal(Math.round(base.terminalGrowth * 100));
      setYears(base.years);
    }
  }, [base]);

  const custom = useMemo(() => {
    if (!data?.baseFcf || !data.shares) return null;
    return intrinsic(data.baseFcf, growth / 100, terminal / 100, discount / 100, years, data.shares);
  }, [data, growth, discount, terminal, years]);

  const customUpside = custom != null && data?.price ? ((custom - data.price) / data.price) * 100 : null;

  if (isLoading) {
    return <Card className="mt-6"><CardHeader><CardTitle>DCF Valuation</CardTitle></CardHeader><CardContent><Skeleton className="h-40 w-full rounded-lg" /></CardContent></Card>;
  }
  if (!data) return null;

  return (
    <Card className="mt-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2"><Calculator className="h-4 w-4 text-primary" /> DCF Valuation</CardTitle>
        {data.price != null && <span className="text-xs text-muted-foreground">Price {formatINR(data.price)}</span>}
      </CardHeader>
      <CardContent className="space-y-4">
        {!data.applicable ? (
          <p className="text-sm text-muted-foreground">{data.note}</p>
        ) : (
          <>
            {/* scenario cards */}
            <div className="grid grid-cols-3 gap-2">
              {data.scenarios.map((s) => (
                <div key={s.name} className="rounded-lg border border-border/60 bg-card/40 p-3 text-center">
                  <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{s.name}</div>
                  <div className="font-mono text-lg font-semibold">{s.intrinsicValue != null ? formatINR(s.intrinsicValue) : "—"}</div>
                  {s.upsidePct != null && (
                    <div className={cn("text-xs font-medium", s.upsidePct >= 0 ? "text-bull" : "text-bear")}>
                      {s.upsidePct >= 0 ? "+" : ""}{s.upsidePct.toFixed(0)}%
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* interactive builder */}
            <div className="rounded-lg border border-border/60 bg-muted/20 p-3">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Build your own</span>
                <div className="text-right">
                  <span className="font-mono text-lg font-bold">{custom != null ? formatINR(custom) : "—"}</span>
                  {customUpside != null && (
                    <span className={cn("ml-2 text-xs font-medium", customUpside >= 0 ? "text-bull" : "text-bear")}>
                      {customUpside >= 0 ? "+" : ""}{customUpside.toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <Slider label="FCF growth" value={growth} min={0} max={25} step={1} suffix="%" onChange={setGrowth} />
                <Slider label="Discount rate" value={discount} min={8} max={18} step={1} suffix="%" onChange={setDiscount} />
                <Slider label="Terminal growth" value={terminal} min={2} max={6} step={1} suffix="%" onChange={setTerminal} />
                <Slider label="Horizon" value={years} min={5} max={15} step={1} suffix="y" onChange={setYears} />
              </div>
            </div>

            <p className="text-[11px] text-muted-foreground">
              Base FCF {data.baseFcf != null ? formatINR(data.baseFcf) : "—"} ({data.fcfSource}). {data.note}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
