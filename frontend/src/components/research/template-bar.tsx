import {
  Award,
  Crosshair,
  FileBarChart,
  Gauge,
  Grid2x2,
  ShieldAlert,
  Target,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface ResearchTemplate {
  label: string;
  icon: typeof Target;
  prompt: (name: string) => string;
}

export const RESEARCH_TEMPLATES: ResearchTemplate[] = [
  {
    label: "Investment Thesis",
    icon: Target,
    prompt: (n) => `Build a complete investment thesis for ${n}: business quality, growth runway, valuation context and what would make the thesis fail.`,
  },
  {
    label: "Risks Analysis",
    icon: ShieldAlert,
    prompt: (n) => `What are the biggest risks for ${n}? Cover business, financial, regulatory and competitive risks, citing the filings.`,
  },
  {
    label: "Management Quality",
    icon: Award,
    prompt: (n) => `Assess the management quality of ${n}: track record, capital allocation, guidance reliability and governance signals from the documents.`,
  },
  {
    label: "Growth Drivers",
    icon: TrendingUp,
    prompt: (n) => `What are the main revenue growth drivers for ${n} over the next few years, according to management commentary and filings?`,
  },
  {
    label: "Competitive Advantage",
    icon: Crosshair,
    prompt: (n) => `What is ${n}'s competitive advantage (moat)? How durable is it versus peers?`,
  },
  {
    label: "Valuation Summary",
    icon: Gauge,
    prompt: (n) => `Summarize the valuation picture for ${n} using the available metrics and peer comparison. Is it expensive or cheap relative to its history and peers?`,
  },
  {
    label: "Earnings Summary",
    icon: FileBarChart,
    prompt: (n) => `Summarize ${n}'s latest reported results: revenue, profitability, margins, and what changed versus the previous period.`,
  },
  {
    label: "SWOT Analysis",
    icon: Grid2x2,
    prompt: (n) => `Do a SWOT analysis of ${n} (strengths, weaknesses, opportunities, threats) grounded in the documents and data.`,
  },
  {
    label: "Bull Case",
    icon: TrendingUp,
    prompt: (n) => `Make the strongest evidence-based bull case for ${n}: what has to go right, and what the upside looks like if it does.`,
  },
  {
    label: "Bear Case",
    icon: ShieldAlert,
    prompt: (n) => `Make the strongest evidence-based bear case for ${n}: what could go wrong, early warning signs, and the downside scenario.`,
  },
  {
    label: "DCF Assumptions",
    icon: Gauge,
    prompt: (n) => `Summarize the key assumptions a DCF for ${n} would rest on (revenue growth, margins, reinvestment, terminal growth) based on the available data — do not invent precise numbers where data is missing.`,
  },
];

interface TemplateBarProps {
  companyName: string;
  disabled: boolean;
  onPick: (prompt: string) => void;
  className?: string;
}

/** Quick-action research templates rendered as a horizontally scrollable chip row. */
export function TemplateBar({ companyName, disabled, onPick, className }: TemplateBarProps) {
  return (
    <div className={cn("flex gap-2 overflow-x-auto pb-1 [scrollbar-width:thin]", className)}>
      {RESEARCH_TEMPLATES.map(({ label, icon: Icon, prompt }) => (
        <button
          key={label}
          type="button"
          disabled={disabled}
          onClick={() => onPick(prompt(companyName))}
          className="flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg border border-border/70 bg-secondary/40 px-2.5 py-1.5 text-[11px] font-medium text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground disabled:opacity-50"
        >
          <Icon className="h-3 w-3 text-primary" />
          {label}
        </button>
      ))}
    </div>
  );
}
