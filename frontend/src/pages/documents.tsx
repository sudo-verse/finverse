import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { BookOpen, Download, FileText, FolderOpen, Leaf, Megaphone, Search, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { StockSearch } from "@/components/shared/stock-search";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getAnnouncements, getAnnualReports, getBoardMeetings, getBrsr } from "@/api/services";
import { useCorporateData } from "@/hooks/queries";

const DEFAULT_SYMBOL = "TCS";

interface DocRow {
  title: string;
  meta: string;
  url: string | null;
}

const CATEGORIES = [
  { key: "annual", label: "Annual Reports", icon: BookOpen },
  { key: "announcements", label: "Announcements", icon: Megaphone },
  { key: "meetings", label: "Board Meetings", icon: FileText },
  { key: "brsr", label: "BRSR / ESG", icon: Leaf },
] as const;

type CategoryKey = (typeof CATEGORIES)[number]["key"];

/** Document Center — every NSE filing for a company in one place, with
 *  search, download links, and a bridge into the AI Research Copilot. */
export default function DocumentsPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const activeSymbol = (symbol ?? DEFAULT_SYMBOL).toUpperCase();
  const [category, setCategory] = useState<CategoryKey>("annual");
  const [query, setQuery] = useState("");

  const annual = useCorporateData("annual-reports", activeSymbol, (s) => getAnnualReports(s, 20), category === "annual");
  const announcements = useCorporateData("announcements-50", activeSymbol, (s) => getAnnouncements(s, 50), category === "announcements");
  const meetings = useCorporateData("board-meetings", activeSymbol, (s) => getBoardMeetings(s, 20), category === "meetings");
  const brsr = useCorporateData("brsr", activeSymbol, getBrsr, category === "brsr");

  const { rows, loading } = useMemo((): { rows: DocRow[]; loading: boolean } => {
    switch (category) {
      case "annual":
        return {
          loading: annual.isLoading,
          rows: (annual.data ?? []).map((r) => ({
            title: `Annual Report ${r.fromYear ?? ""}–${r.toYear ?? ""}`.trim(),
            meta: [r.companyName, r.fileSize].filter(Boolean).join(" · "),
            url: r.fileUrl,
          })),
        };
      case "announcements":
        return {
          loading: announcements.isLoading,
          rows: (announcements.data ?? []).map((a) => ({
            title: a.subject ?? "Announcement",
            meta: [a.broadcastAt, a.details?.slice(0, 120)].filter(Boolean).join(" · "),
            url: a.attachmentUrl,
          })),
        };
      case "meetings":
        return {
          loading: meetings.isLoading,
          rows: (meetings.data ?? []).map((m) => ({
            title: m.purpose ?? "Board Meeting",
            meta: [m.date, m.description?.slice(0, 120)].filter(Boolean).join(" · "),
            url: m.attachmentUrl,
          })),
        };
      case "brsr":
        return {
          loading: brsr.isLoading,
          rows: (brsr.data ?? []).map((b) => ({
            title: `BRSR ${b.fyFrom ?? ""}–${b.fyTo ?? ""}`.trim(),
            meta: [b.submittedAt, b.fileSize].filter(Boolean).join(" · "),
            url: b.attachmentUrl,
          })),
        };
    }
  }, [category, annual, announcements, meetings, brsr]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => r.title.toLowerCase().includes(q) || r.meta.toLowerCase().includes(q));
  }, [rows, query]);

  return (
    <div>
      <PageHeader
        title="Document Center"
        description="Filings, reports and disclosures — live from NSE"
        actions={<StockSearch className="w-full sm:w-80" onSelect={(sym) => navigate(`/documents/${sym}`)} />}
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Badge variant="secondary" className="gap-1.5 font-mono text-sm normal-case">
          <FolderOpen className="h-3.5 w-3.5" /> {activeSymbol}
        </Badge>
        <Tabs value={category} onValueChange={(v) => setCategory(v as CategoryKey)}>
          <TabsList>
            {CATEGORIES.map(({ key, label, icon: Icon }) => (
              <TabsTrigger key={key} value={key} className="gap-1.5">
                <Icon className="h-3.5 w-3.5" /> {label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <div className="relative ml-auto w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search documents…" className="pl-9" />
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to={`/research/${activeSymbol}`}>
            <Sparkles className="h-3.5 w-3.5" /> Ask AI about filings
          </Link>
        </Button>
      </div>

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="divide-y divide-border/50 overflow-hidden">
          {loading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <p className="py-16 text-center text-sm text-muted-foreground">
              {query ? `No documents match "${query}"` : "No documents available in this category"}
            </p>
          ) : (
            filtered.map((doc, i) => (
              <div key={`${doc.title}-${i}`} className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-accent/40">
                <FileText className="h-4 w-4 shrink-0 text-primary" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{doc.title}</p>
                  {doc.meta && <p className="truncate text-xs text-muted-foreground">{doc.meta}</p>}
                </div>
                {doc.url && (
                  <Button asChild variant="ghost" size="sm" className="shrink-0">
                    <a href={doc.url} target="_blank" rel="noreferrer">
                      <Download className="h-3.5 w-3.5" /> Open
                    </a>
                  </Button>
                )}
              </div>
            ))
          )}
        </Card>
      </motion.div>

      <p className="mt-3 text-center text-[11px] text-muted-foreground/70">
        To make a filing searchable by the AI Research Copilot, download it into{" "}
        <code className="rounded bg-muted px-1 py-0.5 text-[10px]">documents/{activeSymbol}/…</code> and run the
        ingestion pipeline.
      </p>
    </div>
  );
}
