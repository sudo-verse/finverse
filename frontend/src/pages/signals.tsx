import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, SearchX, Search } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { PerformanceCard } from "@/components/signals/performance-card";
import { SentimentDot, SignalBadge } from "@/components/shared/signal-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useSignalFacets, useSignals } from "@/hooks/queries";
import { useDebounce } from "@/hooks/use-debounce";
import { formatDateTime, stripHtml } from "@/lib/format";
import type { Sentiment, SignalType } from "@/types";

export default function SignalsPage() {
  const [search, setSearch] = useState("");
  const [signal, setSignal] = useState<string>("ALL");
  const [source, setSource] = useState<string>("ALL");
  const [sentiment, setSentiment] = useState<string>("ALL");
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebounce(search);
  const { data: facets } = useSignalFacets();

  // Filter changes always restart from the first page
  const applyFilter = <T,>(setter: (v: T) => void) => (value: T) => {
    setter(value);
    setPage(1);
  };

  const { data, isLoading, isFetching } = useSignals({
    search: debouncedSearch,
    signal,
    source,
    sentiment,
    page,
    pageSize: 12,
  });

  return (
    <div>
      <PageHeader
        title="Signals"
        description="Event-driven Buy / Sell / Hold signals from the engine"
        actions={
          data && (
            <Badge variant="muted" className="normal-case tracking-normal">
              {data.total} signals
            </Badge>
          )
        }
      />

      {/* Filters */}
      <PerformanceCard />

      <Card className="mb-5 p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => applyFilter(setSearch)(e.target.value)}
              placeholder="Search symbol, company or event…"
              className="pl-9"
            />
          </div>
          <Select value={signal} onValueChange={applyFilter(setSignal)}>
            <SelectTrigger>
              <SelectValue placeholder="Signal type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All signals</SelectItem>
              {(facets?.signals ?? ["BUY", "SELL", "HOLD"]).map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={source} onValueChange={applyFilter(setSource)}>
            <SelectTrigger>
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All sources</SelectItem>
              {(facets?.sources ?? []).map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={sentiment} onValueChange={applyFilter(setSentiment)}>
            <SelectTrigger>
              <SelectValue placeholder="Sentiment" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All sentiment</SelectItem>
              {(facets?.sentiments ?? ["positive", "neutral", "negative"]).map((s) => (
                <SelectItem key={s} value={s} className="capitalize">
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Signal grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full rounded-xl" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div
          className="grid grid-cols-1 gap-4 transition-opacity md:grid-cols-2 xl:grid-cols-3"
          style={{ opacity: isFetching ? 0.6 : 1 }}
        >
          {data.items.map((s, i) => (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: Math.min(i * 0.04, 0.4) }}
            >
              <Link to={s.symbol ? `/stocks/${s.symbol}` : "#"}>
                <Card className="glass-hover flex h-full flex-col gap-3 p-5">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0">
                      <span className="font-mono text-base font-bold">{s.symbol ?? "—"}</span>
                      <p className="line-clamp-1 text-xs text-muted-foreground">{s.companyName ?? s.eventType ?? ""}</p>
                    </div>
                    <SignalBadge signal={s.signal as SignalType} />
                  </div>

                  <p className="line-clamp-2 flex-1 text-sm leading-snug text-foreground/90">
                    {stripHtml(s.eventTitle) || "(no headline)"}
                  </p>

                  <div>
                    <div className="mb-1 flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>Confidence</span>
                      <span className="font-mono tabular">
                        {s.confidence !== null ? `${Math.round(s.confidence * 100)}%` : "—"}
                      </span>
                    </div>
                    <Progress
                      value={(s.confidence ?? 0) * 100}
                      indicatorClassName={
                        s.signal === "BUY" ? "bg-bull" : s.signal === "SELL" ? "bg-bear" : "bg-hold"
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between border-t border-border/50 pt-3 text-[11px] text-muted-foreground">
                    <div className="flex items-center gap-2">
                      {s.sentiment && <SentimentDot sentiment={s.sentiment as Sentiment} withLabel />}
                      <span>·</span>
                      <span>{s.source}</span>
                    </div>
                    <span className="font-mono">{s.timestamp ? formatDateTime(s.timestamp) : ""}</span>
                  </div>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      ) : (
        <Card className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <SearchX className="h-10 w-10 text-muted-foreground/50" />
          <p className="text-sm font-medium">No signals match your filters</p>
          <p className="text-xs text-muted-foreground">
            Try clearing the search — or run the engine: <code className="font-mono">python -m app.main_nse</code>
          </p>
        </Card>
      )}

      {/* Pagination */}
      {data && data.totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-3">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            <ChevronLeft /> Prev
          </Button>
          <span className="font-mono text-xs text-muted-foreground tabular">
            Page {data.page} of {data.totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= data.totalPages} onClick={() => setPage((p) => p + 1)}>
            Next <ChevronRight />
          </Button>
        </div>
      )}
    </div>
  );
}
