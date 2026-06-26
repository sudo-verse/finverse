import { useState } from "react";
import { ExternalLink, FileText, Mic, Sparkles, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useConcalls, useConcallSummary } from "@/hooks/queries";
import type { ConcallSummary } from "@/types";

export function ConcallPanel({ symbol }: { symbol: string }) {
  const { data: concalls, isLoading } = useConcalls(symbol);
  const summarize = useConcallSummary();
  const [summaries, setSummaries] = useState<Record<string, ConcallSummary>>({});
  const [active, setActive] = useState<string | null>(null);

  if (isLoading) {
    return (
      <Card className="mt-6">
        <CardHeader><CardTitle>Earnings Calls</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-20 w-full rounded-lg" /></CardContent>
      </Card>
    );
  }
  if (!concalls || concalls.length === 0) return null;

  const run = (url: string) => {
    setActive(url);
    summarize.mutate(
      { symbol, url },
      { onSuccess: (data) => setSummaries((s) => ({ ...s, [url]: data })) },
    );
  };

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mic className="h-4 w-4 text-primary" /> Earnings Calls
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {concalls.map((c, i) => {
          const url = c.url ?? "";
          const sum = summaries[url];
          const busy = summarize.isPending && active === url;
          return (
            <div key={`${url}-${i}`} className="rounded-lg border border-border/60 bg-card/40 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-sm">
                    <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                    <span className="truncate font-medium">{c.title ?? "Transcript"}</span>
                  </div>
                  <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                    {c.date && <span>{c.date}</span>}
                    {url && (
                      <a href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-primary/80 hover:text-primary">
                        PDF <ExternalLink className="h-2.5 w-2.5" />
                      </a>
                    )}
                  </div>
                </div>
                {url && (
                  <Button size="sm" variant="outline" disabled={busy} onClick={() => run(url)}>
                    {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                    {sum ? "Re-summarize" : "AI Summary"}
                  </Button>
                )}
              </div>

              {busy && <Skeleton className="mt-3 h-24 w-full rounded-lg" />}
              {sum && !busy && (sum.highlights.length > 0 || sum.guidance) && (
                <div className="mt-3 space-y-2 border-t border-border/40 pt-3 text-sm">
                  {sum.highlights.length > 0 && (
                    <div>
                      <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Highlights</div>
                      <ul className="space-y-0.5">{sum.highlights.map((h, j) => <li key={j} className="text-muted-foreground">• {h}</li>)}</ul>
                    </div>
                  )}
                  {sum.guidance && (
                    <p><span className="text-xs font-semibold uppercase tracking-wide text-bull">Guidance:</span> <span className="text-muted-foreground">{sum.guidance}</span></p>
                  )}
                  {sum.outlook && (
                    <p><span className="text-xs font-semibold uppercase tracking-wide text-blue-400">Outlook:</span> <span className="text-muted-foreground">{sum.outlook}</span></p>
                  )}
                  {sum.risks.length > 0 && (
                    <div>
                      <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-400">Risks</div>
                      <ul className="space-y-0.5">{sum.risks.map((r, j) => <li key={j} className="text-muted-foreground">• {r}</li>)}</ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
        <p className="text-[11px] text-muted-foreground">AI summaries are generated from the transcript PDF (Gemini) and cached. Not advice.</p>
      </CardContent>
    </Card>
  );
}
