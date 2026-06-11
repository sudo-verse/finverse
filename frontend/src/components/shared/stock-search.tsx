import { useMemo, useRef, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useStocks } from "@/hooks/queries";
import { cn } from "@/lib/utils";

interface StockSearchProps {
  onSelect: (symbol: string) => void;
  placeholder?: string;
  className?: string;
}

/** Typeahead stock picker used by Stock Analysis and Competitor pages. */
export function StockSearch({ onSelect, placeholder = "Search NSE stocks…", className }: StockSearchProps) {
  const { data: stocks } = useStocks();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const blurTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q || !stocks) return [];
    return stocks
      .filter((s) => s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q))
      .slice(0, 8);
  }, [query, stocks]);

  return (
    <div className={cn("relative", className)}>
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          blurTimer.current = setTimeout(() => setOpen(false), 150);
        }}
        placeholder={placeholder}
        className="pl-9"
      />
      {open && results.length > 0 && (
        <div className="absolute z-30 mt-1.5 w-full overflow-hidden rounded-lg border border-border bg-popover shadow-2xl">
          {results.map((s) => (
            <button
              key={s.symbol}
              type="button"
              onMouseDown={() => {
                clearTimeout(blurTimer.current);
                setQuery("");
                setOpen(false);
                onSelect(s.symbol);
              }}
              className="flex w-full cursor-pointer items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors hover:bg-accent"
            >
              <span className="w-24 shrink-0 font-mono text-xs font-semibold text-primary">{s.symbol}</span>
              <span className="truncate text-muted-foreground">{s.name}</span>
              <span className="ml-auto shrink-0 text-[10px] uppercase tracking-wide text-muted-foreground/70">
                {s.industry}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
