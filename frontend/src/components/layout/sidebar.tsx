import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowLeftRight,
  BarChart3,
  Boxes,
  CalendarClock,
  CalendarDays,
  CandlestickChart,
  Coins,
  Crown,
  ChevronLeft,
  FolderOpen,
  Gauge,
  Landmark,
  Layers,
  LayoutDashboard,
  LineChart,
  Megaphone,
  Microscope,
  Rocket,
  Radar,
  Scale,
  Settings,
  SlidersHorizontal,
  Star,
  Swords,
  Target,
  TrendingUp,
  UserCheck,
  Wallet,
} from "lucide-react";
import { useMarketOverview } from "@/hooks/queries";
import { cn } from "@/lib/utils";

/** NSE market-status codes → label + whether trading is live. */
const MARKET_STATUS: Record<string, { label: string; live: boolean }> = {
  O: { label: "Market Open", live: true },
  PO: { label: "Pre-Open", live: true },
  PC: { label: "Market Closed", live: false },
  C: { label: "Market Closed", live: false },
};

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/conviction", label: "Conviction Score", icon: Target },
  { to: "/watchlist", label: "Watchlist", icon: Star },
  { to: "/screener", label: "Screener", icon: SlidersHorizontal },
  { to: "/baskets", label: "Baskets", icon: Boxes },
  { to: "/valuation", label: "Fair Value", icon: Scale },
  { to: "/ownership", label: "Smart Money", icon: Landmark },
  { to: "/insider", label: "Insider & SAST", icon: UserCheck },
  { to: "/superstars", label: "Marquee Investors", icon: Crown },
  { to: "/announcements", label: "Announcements", icon: Megaphone },
  { to: "/deals", label: "Bulk & Block Deals", icon: ArrowLeftRight },
  { to: "/ipos", label: "IPO Tracker", icon: Rocket },
  { to: "/events", label: "Events Calendar", icon: CalendarDays },
  { to: "/results", label: "Results Calendar", icon: CalendarClock },
  { to: "/dividends", label: "Dividends", icon: Coins },
  { to: "/radar", label: "52-Week Radar", icon: Radar },
  { to: "/earnings", label: "Earnings Momentum", icon: BarChart3 },
  { to: "/technicals", label: "Technicals", icon: CandlestickChart },
  { to: "/fno", label: "F&O / Derivatives", icon: Layers },
  { to: "/signals", label: "Signals", icon: Activity },
  { to: "/sentiment", label: "Sentiment", icon: Gauge },
  { to: "/stocks", label: "Stock Analysis", icon: LineChart },
  { to: "/competitors", label: "Competitors", icon: Swords },
  { to: "/portfolio", label: "Portfolio", icon: Wallet },
  { to: "/research", label: "AI Research", icon: Microscope },
  { to: "/documents", label: "Documents", icon: FolderOpen },
  { to: "/settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { data: market } = useMarketOverview();
  const status = market?.marketStatus ? (MARKET_STATUS[market.marketStatus] ?? { label: market.marketStatus, live: false }) : null;

  return (
    <motion.aside
      animate={{ width: collapsed ? 68 : 232 }}
      transition={{ duration: 0.22, ease: "easeInOut" }}
      className="relative z-30 hidden h-screen shrink-0 flex-col border-r border-border/60 bg-card/40 md:flex"
    >
      {/* Brand */}
      <div className="flex h-16 items-center gap-3 px-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-600">
          <TrendingUp className="h-5 w-5 text-white" />
        </div>
        {!collapsed && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="leading-tight">
            <div className="text-[15px] font-bold tracking-tight">Finverse</div>
            <div className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
              NSE Intelligence
            </div>
          </motion.div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-md px-2.5 py-2 text-[13px] font-medium transition-colors",
                isActive
                  ? "bg-white/[0.06] text-foreground"
                  : "text-muted-foreground hover:bg-white/[0.03] hover:text-foreground",
              )
            }
          >
            <Icon className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Market status + collapse */}
      <div className="space-y-3 border-t border-border/60 p-3">
        {!collapsed && (
          <div className="flex items-center gap-2 rounded-lg bg-secondary/50 px-3 py-2">
            <span className="relative flex h-2 w-2">
              {status?.live && (
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-bull opacity-60" />
              )}
              <span
                className={cn(
                  "relative inline-flex h-2 w-2 rounded-full",
                  status ? (status.live ? "bg-bull" : "bg-hold") : "bg-muted-foreground/50",
                )}
              />
            </span>
            <span className="text-xs text-muted-foreground">NSE · {status?.label ?? "connecting…"}</span>
          </div>
        )}
        <button
          type="button"
          onClick={onToggle}
          className="flex w-full cursor-pointer items-center justify-center rounded-lg py-2 text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform duration-300", collapsed && "rotate-180")} />
        </button>
      </div>
    </motion.aside>
  );
}

export { NAV_ITEMS };
