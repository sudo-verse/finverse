import { History, MessageSquareText, Swords } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useResearchHistory } from "@/hooks/queries";
import { timeAgo } from "@/lib/format";
import type { ResearchHistoryItem } from "@/types";

interface HistoryDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPick: (item: ResearchHistoryItem) => void;
}

/** Past research Q&A (persisted server-side). Picking an item reloads the
 *  exchange into the chat. */
export function HistoryDrawer({ open, onOpenChange, onPick }: HistoryDrawerProps) {
  const { data, isLoading } = useResearchHistory(open);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogTitle className="flex items-center gap-2 text-base font-semibold">
          <History className="h-4 w-4 text-primary" /> Research History
        </DialogTitle>
        <DialogDescription className="text-xs text-muted-foreground">
          Your past copilot conversations — click one to reopen it.
        </DialogDescription>
        <div className="max-h-[60vh] space-y-1.5 overflow-y-auto pr-1">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-lg" />)
          ) : !data || data.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No research history yet.</p>
          ) : (
            data.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => onPick(item)}
                className="flex w-full cursor-pointer items-start gap-3 rounded-lg border border-transparent bg-secondary/40 px-3 py-2.5 text-left transition-colors hover:border-primary/40"
              >
                <span className="mt-0.5 shrink-0 text-primary">
                  {item.mode === "compare" ? <Swords className="h-3.5 w-3.5" /> : <MessageSquareText className="h-3.5 w-3.5" />}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-baseline gap-2">
                    <span className="shrink-0 font-mono text-xs font-semibold text-primary">{item.symbol}</span>
                    <span className="truncate text-xs text-muted-foreground">{timeAgo(item.createdAt)}</span>
                  </span>
                  <span className="mt-0.5 block truncate text-sm">{item.question}</span>
                </span>
              </button>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
