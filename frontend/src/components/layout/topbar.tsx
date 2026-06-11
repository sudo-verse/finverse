import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { Bell, Menu, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useMarketOverview } from "@/hooks/queries";
import { formatNumber, formatPercent } from "@/lib/format";
import { NAV_ITEMS } from "./sidebar";
import { cn } from "@/lib/utils";

interface TopbarProps {
  onOpenPalette: () => void;
}

function Tick({ name, value, changePct }: { name: string; value: number | null; changePct: number | null }) {
  if (value === null) return null;
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{name}</span>
      <span className="font-mono text-xs tabular">{formatNumber(value, 2)}</span>
      {changePct !== null && (
        <span className={cn("font-mono text-xs tabular", changePct >= 0 ? "text-bull" : "text-bear")}>
          {formatPercent(changePct)}
        </span>
      )}
    </div>
  );
}

export function Topbar({ onOpenPalette }: TopbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const { data: market } = useMarketOverview();

  return (
    <header className="sticky top-0 z-20 border-b border-border/60 bg-background/70 backdrop-blur-xl">
      <div className="flex h-16 items-center gap-3 px-4 md:px-6">
        {/* Mobile menu */}
        <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMobileOpen((v) => !v)}>
          {mobileOpen ? <X /> : <Menu />}
        </Button>

        {/* Live index ticker (NSE) */}
        <div className="hidden items-center gap-5 lg:flex">
          {market ? (
            <>
              {market.indices.slice(0, 2).map((idx) => (
                <Tick key={idx.name} name={idx.name} value={idx.last} changePct={idx.percChange} />
              ))}
              {market.giftNifty && (
                <Tick name="GIFT NIFTY" value={market.giftNifty.lastPrice} changePct={market.giftNifty.perChange} />
              )}
              {market.usdInr && <Tick name="USD/INR" value={market.usdInr.ltp} changePct={null} />}
            </>
          ) : (
            <span className="text-[11px] uppercase tracking-wider text-muted-foreground/60">
              Connecting to NSE…
            </span>
          )}
        </div>

        <div className="flex-1" />

        {/* Command palette trigger */}
        <button
          type="button"
          onClick={onOpenPalette}
          className="flex h-9 w-full max-w-[260px] cursor-pointer items-center gap-2 rounded-md border border-input bg-secondary/40 px-3 text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground sm:w-64"
        >
          <Search className="h-4 w-4" />
          <span className="flex-1 truncate text-left">Search stocks, pages…</span>
          <kbd className="hidden rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground sm:inline-block">
            Ctrl K
          </kbd>
        </button>

        <Button variant="ghost" size="icon" className="relative" aria-label="Notifications" onClick={() => navigate("/signals")}>
          <Bell />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-bear" />
        </Button>

        <div className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-violet-600 text-xs font-bold text-white shadow-md">
          SK
        </div>
      </div>

      {/* Mobile nav drawer */}
      {mobileOpen && (
        <nav className="grid grid-cols-2 gap-1 border-t border-border/60 p-3 md:hidden">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium",
                  isActive ? "bg-primary/12 text-primary" : "text-muted-foreground hover:bg-accent/60",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  );
}
