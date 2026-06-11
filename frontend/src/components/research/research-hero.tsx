import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, FileSearch, Microscope, Sparkles, Swords, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CompanySearch } from "@/components/research/company-search";
import { cn } from "@/lib/utils";
import type { ResearchCompany } from "@/types";

export const SUGGESTED_QUESTIONS = [
  "Summarize the latest annual report",
  "Explain the business model",
  "What are the key risks?",
  "What are the main growth drivers?",
  "Compare with competitors",
  "Did promoter holding increase?",
];

interface ResearchHeroProps {
  pendingQuestion: string | null;
  onPickSuggestion: (q: string | null) => void;
  onSelect: (company: ResearchCompany) => void;
  onCompare: (a: ResearchCompany, b: ResearchCompany) => void;
}

/** Landing state of /research — hero, big company search, suggested
 *  questions and the entry point into comparison mode. */
export function ResearchHero({ pendingQuestion, onPickSuggestion, onSelect, onCompare }: ResearchHeroProps) {
  const [compareMode, setCompareMode] = useState(false);
  const [pair, setPair] = useState<(ResearchCompany | null)[]>([null, null]);

  const setSlot = (i: number, c: ResearchCompany | null) =>
    setPair((prev) => prev.map((p, j) => (j === i ? c : p)));

  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center pt-10 text-center md:pt-16">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-600 shadow-xl shadow-emerald-500/25"
      >
        <Microscope className="h-7 w-7 text-white" />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="bg-gradient-to-br from-foreground to-foreground/60 bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl"
      >
        Finverse AI Research Copilot
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground md:text-base"
      >
        Ask questions directly from company filings, earnings calls, announcements and financial data — answered like
        an equity research analyst, with sources.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="mt-8 w-full max-w-xl"
      >
        {!compareMode ? (
          <CompanySearch size="lg" autoFocus placeholder="Search a company to research…  e.g. RELIANCE" onSelect={onSelect} />
        ) : (
          <div className="glass space-y-3 rounded-xl p-4 text-left">
            {[0, 1].map((i) =>
              pair[i] ? (
                <div key={i} className="flex items-center gap-3 rounded-lg bg-secondary/50 px-3 py-2.5">
                  <span className="font-mono text-sm font-semibold text-primary">{pair[i]!.symbol}</span>
                  <span className="truncate text-sm text-muted-foreground">{pair[i]!.name}</span>
                  <button
                    type="button"
                    onClick={() => setSlot(i, null)}
                    className="ml-auto cursor-pointer text-muted-foreground hover:text-foreground"
                    aria-label="Remove"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <CompanySearch key={i} placeholder={`Company ${i + 1}…`} onSelect={(c) => setSlot(i, c)} />
              ),
            )}
            <Button
              className="w-full"
              disabled={!pair[0] || !pair[1] || pair[0].symbol === pair[1].symbol}
              onClick={() => onCompare(pair[0]!, pair[1]!)}
            >
              <Swords className="h-4 w-4" /> Compare Companies <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}

        <button
          type="button"
          onClick={() => setCompareMode((v) => !v)}
          className="mt-3 inline-flex cursor-pointer items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          {compareMode ? (
            <>
              <FileSearch className="h-3.5 w-3.5" /> Back to single-company research
            </>
          ) : (
            <>
              <Swords className="h-3.5 w-3.5" /> Compare two companies instead
            </>
          )}
        </button>
      </motion.div>

      {!compareMode && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-10 w-full max-w-xl"
        >
          <p className="mb-3 flex items-center justify-center gap-1.5 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
            <Sparkles className="h-3 w-3 text-primary" /> Suggested Questions
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => onPickSuggestion(pendingQuestion === q ? null : q)}
                className={cn(
                  "cursor-pointer rounded-full border px-3 py-1.5 text-xs transition-colors",
                  pendingQuestion === q
                    ? "border-primary/60 bg-primary/15 text-primary"
                    : "border-border/70 bg-secondary/40 text-muted-foreground hover:border-primary/40 hover:text-foreground",
                )}
              >
                {q}
              </button>
            ))}
          </div>
          {pendingQuestion && (
            <p className="mt-3 text-xs text-primary/90">Now pick a company above — I'll ask this right away.</p>
          )}
        </motion.div>
      )}
    </div>
  );
}
