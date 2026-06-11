import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowDown, ArrowUp, Download, Filter, RotateCcw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { apiClient } from "@/api/client";
import { PageHeader } from "@/components/layout/page-header";
import { scoreColor } from "@/components/sentiment/gauge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { formatFraction, formatINRCompact, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ScreenerRow } from "@/types";

function useScreener() {
  return useQuery({
    queryKey: ["screener"],
    queryFn: async () => (await apiClient.get<ScreenerRow[]>("/screener")).data,
    staleTime: 10 * 60_000,
  });
}

/** Numeric filters: [field, label, kind] — min keeps rows >= value, max <= value. */
const FILTERS = [
  ["pe", "PE max", "max"],
  ["roe", "ROE min %", "min-pct"],
  ["roce", "ROCE min %", "min-pct"],
  ["npm", "NPM min %", "min-pct"],
  ["debtToEquity", "D/E max", "max"],
  ["revenueGrowth", "Rev growth min %", "min-pct"],
  ["profitGrowth", "Profit growth min %", "min-pct"],
  ["sentiment", "Sentiment min", "min"],
] as const;

type FilterField = (typeof FILTERS)[number][0];

const COLUMNS = [
  ["price", "Price"],
  ["marketCap", "M.Cap"],
  ["pe", "PE"],
  ["pb", "PB"],
  ["roe", "ROE"],
  ["roce", "ROCE"],
  ["npm", "NPM"],
  ["debtToEquity", "D/E"],
  ["revenueGrowth", "Rev YoY"],
  ["profitGrowth", "PAT YoY"],
  ["sentiment", "Sent."],
] as const;

type SortField = (typeof COLUMNS)[number][0] | "symbol";

function fmtCell(field: SortField, v: number | null): string {
  if (v === null) return "—";
  if (field === "marketCap") return formatINRCompact(v);
  if (["roe", "roce", "npm", "revenueGrowth", "profitGrowth"].includes(field)) return formatFraction(v);
  if (field === "sentiment") return String(Math.round(v));
  return formatNumber(v, field === "price" ? 1 : 2);
}

export default function ScreenerPage() {
  const { data, isLoading } = useScreener();
  const [filters, setFilters] = useState<Partial<Record<FilterField, string>>>({});
  const [industry, setIndustry] = useState("ALL");
  const [sort, setSort] = useState<SortField>("marketCap");
  const [desc, setDesc] = useState(true);

  const industries = useMemo(
    () => [...new Set((data ?? []).map((r) => r.industry).filter(Boolean) as string[])].sort(),
    [data],
  );

  const rows = useMemo(() => {
    let out = data ?? [];
    if (industry !== "ALL") out = out.filter((r) => r.industry === industry);
    for (const [field, , kind] of FILTERS) {
      const raw = filters[field]?.trim();
      if (!raw) continue;
      const v = Number(raw) / (kind === "min-pct" ? 100 : 1);
      if (Number.isNaN(v)) continue;
      out = out.filter((r) => {
        const x = r[field];
        if (x === null) return false; // a filter on a metric excludes unknowns
        return kind === "max" ? x <= v : x >= v;
      });
    }
    return [...out].sort((a, b) => {
      if (sort === "symbol") return desc ? b.symbol.localeCompare(a.symbol) : a.symbol.localeCompare(b.symbol);
      const av = a[sort], bv = b[sort];
      if (av === null) return 1;
      if (bv === null) return -1;
      return desc ? bv - av : av - bv;
    });
  }, [data, filters, industry, sort, desc]);

  const exportCsv = () => {
    const cols: SortField[] = ["symbol", ...COLUMNS.map(([f]) => f)];
    const csv = [
      cols.join(","),
      ...rows.map((r) => cols.map((c) => (c === "symbol" ? r.symbol : (r[c] ?? ""))).join(",")),
    ].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: "finverse-screen.csv" });
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Exported ${rows.length} rows`);
  };

  const header = (field: SortField, label: string) => (
    <th
      key={field}
      className="cursor-pointer whitespace-nowrap px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground"
      onClick={() => {
        if (sort === field) setDesc((d) => !d);
        else {
          setSort(field);
          setDesc(true);
        }
      }}
    >
      <span className="inline-flex items-center gap-0.5">
        {label}
        {sort === field && (desc ? <ArrowDown className="h-3 w-3" /> : <ArrowUp className="h-3 w-3" />)}
      </span>
    </th>
  );

  return (
    <div>
      <PageHeader
        title="Screener"
        description="Filter the NIFTY-500 universe by fundamentals, valuation and sentiment"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setFilters({})}>
              <RotateCcw className="h-3.5 w-3.5" /> Reset
            </Button>
            <Button variant="outline" size="sm" onClick={exportCsv} disabled={rows.length === 0}>
              <Download className="h-3.5 w-3.5" /> CSV
            </Button>
          </div>
        }
      />

      {/* Filters */}
      <Card className="mb-4 p-4">
        <p className="mb-3 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          <Filter className="h-3 w-3 text-primary" /> Filters
          <span className="ml-auto font-mono normal-case tracking-normal">
            {rows.length} / {data?.length ?? 0} stocks
          </span>
        </p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9">
          <Select value={industry} onValueChange={setIndustry}>
            <SelectTrigger className="h-9 text-xs">
              <SelectValue placeholder="Industry" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All industries</SelectItem>
              {industries.map((i) => (
                <SelectItem key={i} value={i}>
                  {i}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {FILTERS.map(([field, label]) => (
            <Input
              key={field}
              type="number"
              placeholder={label}
              value={filters[field] ?? ""}
              onChange={(e) => setFilters((f) => ({ ...f, [field]: e.target.value }))}
              className="h-9 text-xs"
            />
          ))}
        </div>
      </Card>

      {/* Results */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="overflow-x-auto">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full rounded-lg" />
              ))}
            </div>
          ) : (
            <table className="w-full text-xs">
              <thead className="border-b border-border/60">
                <tr>
                  <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Stock
                  </th>
                  {COLUMNS.map(([f, l]) => header(f, l))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 100).map((r) => (
                  <tr key={r.symbol} className="border-b border-border/40 transition-colors last:border-0 hover:bg-accent/40">
                    <td className="px-3 py-2">
                      <Link to={`/stocks/${r.symbol}`} className="group">
                        <span className="font-mono font-semibold text-primary group-hover:underline">{r.symbol}</span>
                        <span className="block max-w-44 truncate text-[10px] text-muted-foreground">{r.industry}</span>
                      </Link>
                    </td>
                    {COLUMNS.map(([f]) => (
                      <td
                        key={f}
                        className={cn(
                          "whitespace-nowrap px-3 py-2 text-right font-mono tabular",
                          (f === "revenueGrowth" || f === "profitGrowth") &&
                            r[f] !== null &&
                            (r[f]! >= 0 ? "text-bull" : "text-bear"),
                        )}
                        style={f === "sentiment" && r.sentiment !== null ? { color: scoreColor(r.sentiment) } : undefined}
                      >
                        {fmtCell(f, r[f])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!isLoading && rows.length > 100 && (
            <p className="border-t border-border/40 py-2 text-center text-[10px] text-muted-foreground">
              Showing top 100 of {rows.length} — tighten filters or export CSV for the full list.
            </p>
          )}
        </Card>
      </motion.div>
      <p className="mt-2 text-center text-[10px] text-muted-foreground/70">
        PE/PB use each company's filing currency (Yahoo) — unreliable for the few USD filers. Ratios and growth are
        currency-agnostic.
      </p>
    </div>
  );
}
