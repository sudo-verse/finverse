import { useMemo, useRef, useState } from "react";
import { FileText, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useResearchCompanies } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import type { ResearchCompany } from "@/types";

interface CompanySearchProps {
  onSelect: (company: ResearchCompany) => void;
  placeholder?: string;
  size?: "default" | "lg";
  className?: string;
  autoFocus?: boolean;
}

/** Research-aware company picker: surfaces how many document chunks are
 *  indexed for each company so users know where the copilot is strongest. */
export function CompanySearch({
  onSelect,
  placeholder = "Search NSE companies…",
  size = "default",
  className,
  autoFocus,
}: CompanySearchProps) {
  const { data: companies } = useResearchCompanies();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const blurTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q || !companies) return [];
    return companies
      .filter((c) => c.symbol.toLowerCase().includes(q) || c.name.toLowerCase().includes(q))
      .sort((a, b) => b.indexedChunks - a.indexedChunks)
      .slice(0, 8);
  }, [query, companies]);

  return (
    <div className={cn("relative", className)}>
      <Search
        className={cn(
          "absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground",
          size === "lg" ? "h-5 w-5 left-4" : "h-4 w-4",
        )}
      />
      <Input
        value={query}
        autoFocus={autoFocus}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          blurTimer.current = setTimeout(() => setOpen(false), 150);
        }}
        placeholder={placeholder}
        className={cn(size === "lg" ? "h-13 rounded-xl pl-12 text-base shadow-lg shadow-primary/5" : "pl-9")}
      />
      {open && results.length > 0 && (
        <div className="absolute z-30 mt-1.5 w-full overflow-hidden rounded-xl border border-border bg-popover shadow-2xl">
          {results.map((c) => (
            <button
              key={c.symbol}
              type="button"
              onMouseDown={() => {
                clearTimeout(blurTimer.current);
                setQuery("");
                setOpen(false);
                onSelect(c);
              }}
              className="flex w-full cursor-pointer items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors hover:bg-accent"
            >
              <span className="w-24 shrink-0 font-mono text-xs font-semibold text-primary">{c.symbol}</span>
              <span className="truncate text-muted-foreground">{c.name}</span>
              <span className="ml-auto flex shrink-0 items-center gap-1 text-[10px] text-muted-foreground/80">
                {c.indexedChunks > 0 && (
                  <>
                    <FileText className="h-2.5 w-2.5" />
                    {c.indexedChunks} chunks
                  </>
                )}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
