import { Link } from "react-router-dom";
import { useMarquee } from "@/hooks/queries";
import { formatNumber, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Scrolling NIFTY 50 constituents tape (NSE marquee feed), under the topbar. */
export function TickerTape() {
  const { data } = useMarquee();
  if (!data || data.length === 0) return null;

  // duplicate the list so the CSS loop is seamless
  const items = [...data, ...data];

  return (
    <div className="relative z-10 overflow-hidden border-b border-border/60 bg-card/40 backdrop-blur-xl">
      <div className="animate-ticker flex w-max items-center gap-6 px-4 py-1.5">
        {items.map((m, i) => (
          <Link
            key={`${m.symbol}-${i}`}
            to={`/stocks/${m.symbol}`}
            className="flex shrink-0 items-baseline gap-1.5 text-[11px] transition-opacity hover:opacity-75"
          >
            <span className="font-mono font-semibold text-foreground/80">{m.symbol}</span>
            <span className="font-mono tabular text-muted-foreground">
              {m.lastPrice !== null ? formatNumber(m.lastPrice, 2) : "—"}
            </span>
            {m.perChange !== null && (
              <span className={cn("font-mono tabular", m.perChange >= 0 ? "text-bull" : "text-bear")}>
                {formatPercent(m.perChange)}
              </span>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
