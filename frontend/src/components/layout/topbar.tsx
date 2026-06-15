import { useRef, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Bell, BellOff, LogOut, Menu, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth";
import { useAlertEvents, useMarkAlertsSeen, useMarketOverview } from "@/hooks/queries";
import { formatNumber, formatPercent, timeAgo } from "@/lib/format";
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

function AlertsBell() {
  const [open, setOpen] = useState(false);
  const { data: events } = useAlertEvents();
  const markSeen = useMarkAlertsSeen();
  const blurTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const unseen = events?.filter((e) => !e.seen).length ?? 0;

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next && unseen > 0) markSeen.mutate();
  };

  return (
    <div
      className="relative"
      onBlur={() => {
        blurTimer.current = setTimeout(() => setOpen(false), 150);
      }}
      onFocus={() => clearTimeout(blurTimer.current)}
    >
      <Button variant="ghost" size="icon" className="relative" aria-label="Alerts" onClick={toggle}>
        <Bell />
        {unseen > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-bear px-1 font-mono text-[9px] font-bold text-white">
            {unseen}
          </span>
        )}
      </Button>
      {open && (
        <div className="absolute right-0 top-11 z-40 w-80 overflow-hidden rounded-xl border border-border bg-popover shadow-2xl">
          <div className="flex items-center justify-between border-b border-border/60 px-3 py-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Alerts</span>
            <Link to="/watchlist" className="text-[11px] text-primary hover:underline" onClick={() => setOpen(false)}>
              Manage →
            </Link>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {!events || events.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-8 text-center">
                <BellOff className="h-6 w-6 text-muted-foreground/40" />
                <p className="px-6 text-xs text-muted-foreground">
                  No alerts fired yet. Create rules from your watchlist.
                </p>
              </div>
            ) : (
              events.map((e) => (
                <Link
                  key={e.id}
                  to={`/stocks/${e.symbol}`}
                  onClick={() => setOpen(false)}
                  className="block border-b border-border/40 px-3 py-2.5 transition-colors last:border-0 hover:bg-accent/40"
                >
                  <span className="flex items-baseline gap-2">
                    <span className="font-mono text-xs font-semibold text-primary">{e.symbol}</span>
                    <span className="text-[10px] text-muted-foreground">{timeAgo(e.createdAt)}</span>
                  </span>
                  <span className="mt-0.5 block text-xs leading-snug text-foreground/85">{e.message}</span>
                </Link>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const blurTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  if (!user) return null;

  const initials =
    (user.fullName || user.email)
      .split(/[\s@.]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((s) => s[0]?.toUpperCase())
      .join("") || "U";

  return (
    <div
      className="relative"
      onBlur={() => {
        blurTimer.current = setTimeout(() => setOpen(false), 150);
      }}
      onFocus={() => clearTimeout(blurTimer.current)}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Account menu"
        className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-violet-600 text-xs font-bold text-white shadow-md"
      >
        {initials}
      </button>
      {open && (
        <div className="absolute right-0 top-11 z-40 w-56 overflow-hidden rounded-xl border border-border bg-popover shadow-2xl">
          <div className="border-b border-border/60 px-3 py-2.5">
            <p className="truncate text-sm font-medium">{user.fullName || "Account"}</p>
            <p className="truncate text-xs text-muted-foreground">{user.email}</p>
            <span className="mt-1 inline-block rounded bg-primary/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-primary">
              {user.plan}
            </span>
          </div>
          <button
            type="button"
            onClick={logout}
            className="flex w-full cursor-pointer items-center gap-2 px-3 py-2.5 text-sm text-foreground/85 transition-colors hover:bg-accent/40"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}

export function Topbar({ onOpenPalette }: TopbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
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

        <AlertsBell />
        <UserMenu />
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
