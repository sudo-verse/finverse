import { useState } from "react";
import { BookOpen, ExternalLink, FileText, Newspaper, Presentation } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import type { SourceCitation } from "@/types";

/** doc_type → folder under documents/<SYMBOL>/ (mirrors the ingestion pipeline). */
const DOC_TYPE_FOLDERS: Record<string, string> = {
  annual_report: "annual_reports",
  quarterly_report: "quarterly_reports",
  earnings_call: "earnings_calls",
  presentation: "presentations",
  announcement: "announcements",
  financials: "financials",
};

const DOC_TYPE_ICONS: Record<string, typeof FileText> = {
  annual_report: BookOpen,
  presentation: Presentation,
  news: Newspaper,
};

function documentUrl(citation: SourceCitation, fallbackSymbol: string): string | null {
  const folder = DOC_TYPE_FOLDERS[citation.docType ?? ""];
  const symbol = citation.symbol ?? fallbackSymbol;
  if (!folder || !symbol) return null;
  const page = citation.page ? `#page=${citation.page}` : "";
  return `/docfiles/${symbol}/${folder}/${encodeURIComponent(citation.source)}${page}`;
}

interface SourceCitationsProps {
  sources: SourceCitation[];
  symbol: string;
}

/** "Sources Used" footer of an assistant answer. Each citation opens a dialog
 *  with the supporting excerpt and (when the file exists locally) a link to
 *  the original document at the cited page. */
export function SourceCitations({ sources, symbol }: SourceCitationsProps) {
  const [selected, setSelected] = useState<SourceCitation | null>(null);

  if (sources.length === 0) return null;

  return (
    <div className="pt-3">
      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Sources Used</p>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((s, i) => {
          const Icon = DOC_TYPE_ICONS[s.docType ?? ""] ?? FileText;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => setSelected(s)}
              className="flex cursor-pointer items-center gap-1.5 rounded-lg border border-border/70 bg-secondary/40 px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
            >
              <span className="font-mono text-[10px] font-semibold text-primary">[{i + 1}]</span>
              <Icon className="h-3 w-3" />
              <span className="max-w-44 truncate">
                {s.symbol ? `${s.symbol} · ` : ""}
                {s.label}
              </span>
            </button>
          );
        })}
      </div>

      <Dialog open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-xl">
          {selected && (
            <>
              <DialogTitle className="pr-8 text-base font-semibold">
                {selected.symbol ? `${selected.symbol} — ` : ""}
                {selected.label}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                {selected.source}
                {selected.page ? ` · page ${selected.page}` : ""}
              </DialogDescription>
              <blockquote className="max-h-64 overflow-y-auto rounded-lg border-l-2 border-primary/50 bg-secondary/40 p-3 text-sm leading-relaxed text-foreground/85">
                {selected.snippet}…
              </blockquote>
              {(() => {
                const url = documentUrl(selected, symbol);
                return url ? (
                  <Button asChild variant="outline" size="sm" className="w-fit">
                    <a href={url} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-3.5 w-3.5" /> Open document
                    </a>
                  </Button>
                ) : null;
              })()}
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
