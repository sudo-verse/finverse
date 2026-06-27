import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { TickerTape } from "./ticker-tape";
import { Footer } from "./footer";
import { CommandPalette } from "./command-palette";

/** First path segment → document title for authenticated pages. */
const ROUTE_TITLES: Record<string, string> = {
  "": "Dashboard",
  watchlist: "Watchlist",
  screener: "Screener",
  valuation: "Fair Value",
  ownership: "Smart Money",
  insider: "Insider & SAST",
  announcements: "Announcements",
  deals: "Bulk & Block Deals",
  events: "Events Calendar",
  radar: "52-Week Radar",
  earnings: "Earnings Momentum",
  signals: "Signals",
  sentiment: "Sentiment",
  stocks: "Stock Analysis",
  competitors: "Competitors",
  portfolio: "Portfolio",
  research: "AI Research",
  documents: "Documents",
  settings: "Settings",
};

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const seg = location.pathname.split("/")[1] ?? "";
    const label = ROUTE_TITLES[seg];
    document.title = label ? `${label} · Finverse` : "Finverse — AI Stock Intelligence for the NSE";
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <Topbar onOpenPalette={() => setPaletteOpen(true)} />
        <TickerTape />
        <main className="flex-1 p-4 md:p-6 lg:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
              className="mx-auto w-full max-w-[1500px]"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
        <Footer />
      </div>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </div>
  );
}
