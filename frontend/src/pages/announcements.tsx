import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ExternalLink, FileText, Megaphone, Search } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnnouncementsFeed } from "@/hooks/queries";
import { timeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";

const CATS: { key: string; label: string }[] = [
  { key: "", label: "All" },
  { key: "result", label: "Results" },
  { key: "order", label: "Orders" },
  { key: "rating", label: "Ratings" },
  { key: "fundraise", label: "Fundraise" },
  { key: "mna", label: "M&A" },
  { key: "dividend", label: "Dividend" },
  { key: "buyback", label: "Buyback" },
  { key: "board", label: "Board" },
  { key: "agm", label: "AGM" },
  { key: "management", label: "Mgmt" },
  { key: "investor", label: "Investor" },
];

const CAT_LABEL: Record<string, string> = {
  result: "Results", order: "Order", rating: "Rating", fundraise: "Fundraise",
  mna: "M&A", dividend: "Dividend", buyback: "Buyback", board: "Board",
  agm: "AGM", management: "Mgmt", investor: "Investor", sast: "SAST",
  other: "Update", routine: "Routine",
};

const CAT_COLOR: Record<string, string> = {
  result: "bg-blue-500/10 text-blue-400 border-blue-500/25",
  order: "bg-bull/10 text-bull border-bull/25",
  rating: "bg-amber-500/10 text-amber-400 border-amber-500/25",
  fundraise: "bg-violet-500/10 text-violet-400 border-violet-500/25",
  mna: "bg-pink-500/10 text-pink-400 border-pink-500/25",
  sast: "bg-pink-500/10 text-pink-400 border-pink-500/25",
  dividend: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
  buyback: "bg-teal-500/10 text-teal-400 border-teal-500/25",
  board: "bg-slate-500/10 text-slate-300 border-slate-500/25",
  agm: "bg-slate-500/10 text-slate-300 border-slate-500/25",
  management: "bg-orange-500/10 text-orange-400 border-orange-500/25",
  investor: "bg-cyan-500/10 text-cyan-400 border-cyan-500/25",
  other: "bg-muted text-muted-foreground border-border/60",
  routine: "bg-muted text-muted-foreground border-border/60",
};

function CategoryTag({ category }: { category: string }) {
  return (
    <span
      className={cn(
        "shrink-0 rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
        CAT_COLOR[category] ?? CAT_COLOR.other,
      )}
    >
      {CAT_LABEL[category] ?? "Update"}
    </span>
  );
}

export default function AnnouncementsPage() {
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const { data, isLoading } = useAnnouncementsFeed({
    category: category || undefined,
    days: 2,
    limit: 200,
  });

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return data ?? [];
    return (data ?? []).filter(
      (r) =>
        (r.name ?? "").toLowerCase().includes(q) ||
        (r.symbol ?? "").toLowerCase().includes(q) ||
        (r.desc ?? "").toLowerCase().includes(q) ||
        (r.detail ?? "").toLowerCase().includes(q),
    );
  }, [data, search]);

  return (
    <div>
      <PageHeader
        title="Corporate Announcements"
        description="Live price-sensitive filings across the market — order wins, rating actions, fund-raising, results and more, classified and de-noised. Sourced from NSE, refreshed every few minutes."
      />

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {CATS.map((c) => (
          <button
            key={c.key}
            onClick={() => setCategory(c.key)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              category === c.key
                ? "border-primary/40 bg-primary/15 text-primary"
                : "border-border/60 text-muted-foreground hover:bg-accent/60 hover:text-foreground",
            )}
          >
            {c.label}
          </button>
        ))}
      </div>

      <div className="relative mt-3 max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search company or filing…"
          className="w-full rounded-lg border border-border/60 bg-card/40 py-2 pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-primary/40"
        />
      </div>

      <Card className="mt-4 divide-y divide-border/40">
        {isLoading ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            {data && data.length > 0
              ? "No announcements match your search."
              : "No announcements available right now — the NSE feed may be rate-limited; it refreshes shortly."}
          </p>
        ) : (
          rows.map((r, i) => (
            <motion.div
              key={`${r.symbol}-${r.broadcastAt}-${i}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-start gap-3 p-3.5 hover:bg-muted/20"
            >
              <CategoryTag category={r.category} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                  {r.symbol ? (
                    <Link to={`/stocks/${r.symbol}`} className="font-mono text-sm font-semibold hover:text-primary">
                      {r.symbol}
                    </Link>
                  ) : (
                    <span className="font-mono text-sm font-semibold">—</span>
                  )}
                  <span className="truncate text-xs text-muted-foreground">{r.name}</span>
                  {r.desc && <span className="text-xs font-medium text-foreground/70">· {r.desc}</span>}
                </div>
                {r.detail && (
                  <p className="mt-0.5 line-clamp-2 text-sm text-muted-foreground">{r.detail}</p>
                )}
                <div className="mt-1 flex items-center gap-3 text-[11px] text-muted-foreground">
                  {r.broadcastAt && <span>{timeAgo(r.broadcastAt)}</span>}
                  {r.industry && <span className="hidden sm:inline">· {r.industry}</span>}
                  {r.attachmentUrl && (
                    <a
                      href={r.attachmentUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-primary/80 hover:text-primary"
                    >
                      <FileText className="h-3 w-3" /> Filing <ExternalLink className="h-2.5 w-2.5" />
                    </a>
                  )}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Megaphone className="h-3.5 w-3.5" />
        Routine notices (trading-window closures, newspaper copies) are hidden. Showing the last ~2 days.
      </p>
    </div>
  );
}
