import { BarChart3, CandlestickChart, Check, FileSearch, Newspaper, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useResearchSources } from "@/hooks/queries";
import { cn } from "@/lib/utils";

function SourceRow({ ok, label, detail }: { ok: boolean; label: string; detail?: string }) {
  return (
    <div className="flex items-center gap-2.5 rounded-lg bg-secondary/40 px-3 py-2">
      <span
        className={cn(
          "flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full",
          ok ? "bg-bull/15 text-bull" : "bg-muted text-muted-foreground/60",
        )}
      >
        {ok ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
      </span>
      <span className={cn("text-xs font-medium", !ok && "text-muted-foreground/70")}>{label}</span>
      {detail && <span className="ml-auto shrink-0 text-[10px] text-muted-foreground">{detail}</span>}
    </div>
  );
}

/** "Available Sources" checklist — what the copilot can actually see for the
 *  selected company (indexed filings + Finverse structured data). */
export function SourcesPanel({ symbol }: { symbol: string }) {
  const { data, isLoading } = useResearchSources(symbol);

  return (
    <Card className="glass-hover">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSearch className="h-4 w-4 text-primary" /> Available Sources
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {isLoading || !data ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <>
            {data.docTypes.map((d) => (
              <SourceRow
                key={d.docType}
                ok
                label={d.label}
                detail={`${d.documents} doc${d.documents === 1 ? "" : "s"}${
                  d.years.length ? ` · ${d.years.slice(0, 3).join(", ")}` : ""
                }`}
              />
            ))}
            <SourceRow
              ok={data.hasFinancials}
              label="Financial Statements"
              detail={data.hasFinancials ? "Finverse DB" : undefined}
            />
            <SourceRow
              ok={data.hasPriceHistory}
              label="Price History & Quant"
              detail={data.hasPriceHistory ? "Finverse DB" : undefined}
            />
            <SourceRow
              ok={data.newsSignals > 0}
              label="News Signals"
              detail={data.newsSignals > 0 ? `${data.newsSignals} signals` : undefined}
            />

            <div className="flex items-center gap-2 pt-2 text-[10px] text-muted-foreground/80">
              <span className="flex items-center gap-1">
                <BarChart3 className="h-3 w-3" /> {data.totalChunks} indexed chunks
              </span>
              <span className="flex items-center gap-1">
                <CandlestickChart className="h-3 w-3" /> live metrics
              </span>
              <span className="flex items-center gap-1">
                <Newspaper className="h-3 w-3" /> signals
              </span>
            </div>
            {data.totalChunks === 0 && (
              <p className="pt-1 text-[11px] leading-relaxed text-muted-foreground">
                No filings indexed yet — drop PDFs into{" "}
                <code className="rounded bg-muted px-1 py-0.5 text-[10px]">documents/{symbol}/annual_reports/</code>{" "}
                and run{" "}
                <code className="rounded bg-muted px-1 py-0.5 text-[10px]">python -m app.etl.ingest_documents</code>.
                Answers will use Finverse structured data meanwhile.
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
