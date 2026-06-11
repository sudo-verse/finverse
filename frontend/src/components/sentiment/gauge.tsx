import { cn } from "@/lib/utils";

export function scoreColor(score: number): string {
  if (score >= 80) return "var(--bull)";
  if (score >= 60) return "#34d399";
  if (score >= 40) return "var(--hold)";
  if (score >= 20) return "#fb7185";
  return "var(--bear)";
}

export function scoreLabel(score: number): string {
  if (score >= 80) return "Strong Buy";
  if (score >= 60) return "Buy";
  if (score >= 40) return "Neutral";
  if (score >= 20) return "Sell";
  return "Strong Sell";
}

interface GaugeProps {
  score: number; // 0-100
  size?: number;
  label?: string;
  sublabel?: string;
  className?: string;
}

/** Semicircular sentiment gauge (0-100) with the Shoonya-style color bands. */
export function SentimentGauge({ score, size = 220, label, sublabel, className }: GaugeProps) {
  const r = size / 2 - 14;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = Math.PI * r; // half circle
  const filled = (Math.max(0, Math.min(100, score)) / 100) * circumference;
  const color = scoreColor(score);

  return (
    <div className={cn("relative flex flex-col items-center", className)} style={{ width: size }}>
      <svg width={size} height={size / 2 + 18} viewBox={`0 0 ${size} ${size / 2 + 18}`}>
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="var(--secondary)"
          strokeWidth={13}
          strokeLinecap="round"
        />
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth={13}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          style={{ transition: "stroke-dasharray 0.8s ease, stroke 0.4s ease" }}
        />
      </svg>
      <div className="absolute bottom-0 flex flex-col items-center">
        <span className="font-mono text-4xl font-bold tabular" style={{ color }}>
          {Math.round(score)}
        </span>
        {label && (
          <span className="text-sm font-bold uppercase tracking-wider" style={{ color }}>
            {label}
          </span>
        )}
        {sublabel && <span className="mt-0.5 text-[11px] text-muted-foreground">{sublabel}</span>}
      </div>
    </div>
  );
}

/** Horizontal score bar used in the pillar breakdown. */
export function ScoreBar({ name, score }: { name: string; score: number | null }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 text-xs font-medium text-muted-foreground">{name}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
        {score !== null && (
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${score}%`, background: scoreColor(score) }}
          />
        )}
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-sm font-semibold tabular">
        {score !== null ? Math.round(score) : "—"}
      </span>
    </div>
  );
}
