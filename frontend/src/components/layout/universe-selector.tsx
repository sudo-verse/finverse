import { Layers } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { usePreferences, UNIVERSES, type Universe } from "@/contexts/preferences";

/**
 * Global stock-universe filter. Persisted in preferences and read by the ranked
 * list pages (Smart Money, Screener, Fair Value, Earnings, 52-Week Radar) to
 * narrow results to an NSE index instead of the full ~2,300-stock universe.
 */
export function UniverseSelector() {
  const { prefs, setUniverse } = usePreferences();
  return (
    <Select value={prefs.universe} onValueChange={(v) => setUniverse(v as Universe)}>
      <SelectTrigger
        className="h-9 w-[112px] gap-1.5 border-input bg-secondary/40 text-xs sm:w-[140px]"
        aria-label="Stock universe"
        title="Personalise which stocks appear in ranked lists"
      >
        <Layers className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {UNIVERSES.map((u) => (
          <SelectItem key={u.key} value={u.key} className="text-xs">
            {u.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
