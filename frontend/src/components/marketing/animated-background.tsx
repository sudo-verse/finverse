import { cn } from "@/lib/utils";

/** Deterministic candlestick row — low-opacity, drifting, finance flavour. */
const CANDLES = [
  { x: 4, o: 48, c: 30, hi: 22, lo: 70, up: true },
  { x: 11, o: 30, c: 40, hi: 24, lo: 52, up: false },
  { x: 18, o: 40, c: 26, hi: 18, lo: 56, up: true },
  { x: 25, o: 26, c: 34, hi: 20, lo: 48, up: false },
  { x: 32, o: 34, c: 22, hi: 14, lo: 44, up: true },
  { x: 39, o: 22, c: 30, hi: 16, lo: 42, up: false },
  { x: 46, o: 30, c: 18, hi: 10, lo: 40, up: true },
  { x: 53, o: 18, c: 28, hi: 12, lo: 38, up: false },
  { x: 60, o: 28, c: 16, hi: 8, lo: 36, up: true },
  { x: 67, o: 16, c: 24, hi: 10, lo: 34, up: false },
  { x: 74, o: 24, c: 12, hi: 6, lo: 30, up: true },
  { x: 81, o: 12, c: 20, hi: 8, lo: 28, up: false },
  { x: 88, o: 20, c: 10, hi: 4, lo: 26, up: true },
  { x: 95, o: 10, c: 16, hi: 6, lo: 24, up: false },
];

const UP = "#10b981";
const DOWN = "#f43f5e";

interface Props {
  className?: string;
  /** Animated grid + glow blobs. */
  grid?: boolean;
  /** The flowing stock price line. */
  priceLine?: boolean;
  /** Drifting candlestick row at the bottom. */
  candles?: boolean;
}

/**
 * Decorative finance-themed background for the dark marketing surface: an
 * animated grid, a flowing stock price line (drawn + a live dashed overlay),
 * drifting candlesticks and soft glow. Purely decorative + pointer-events-none.
 */
export function AnimatedBackground({ className, grid = true, priceLine = true, candles = true }: Props) {
  return (
    <div className={cn("pointer-events-none absolute inset-0 -z-10 overflow-hidden", className)}>
      {/* Drifting grid */}
      {grid && <div className="fv-grid absolute inset-0 opacity-60" />}

      {/* Glow blobs */}
      <div className="absolute -top-32 left-1/4 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl" />
      <div className="absolute top-10 right-1/4 h-80 w-80 rounded-full bg-violet-500/[0.07] blur-3xl" />

      {/* Flowing price line */}
      {priceLine && (
      <svg
        className="absolute inset-x-0 bottom-0 h-[70%] w-full"
        viewBox="0 0 1200 400"
        preserveAspectRatio="none"
        aria-hidden
      >
        <defs>
          <linearGradient id="fv-line" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#60a5fa" stopOpacity="0" />
            <stop offset="50%" stopColor="#60a5fa" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.9" />
          </linearGradient>
          <linearGradient id="fv-area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Area fill */}
        <path
          d="M0,320 L100,300 L200,330 L300,260 L400,290 L500,220 L600,250 L700,180 L800,210 L900,140 L1000,170 L1100,90 L1200,120 L1200,400 L0,400 Z"
          fill="url(#fv-area)"
        />
        {/* Base line (drawn once) */}
        <path
          d="M0,320 L100,300 L200,330 L300,260 L400,290 L500,220 L600,250 L700,180 L800,210 L900,140 L1000,170 L1100,90 L1200,120"
          fill="none"
          stroke="url(#fv-line)"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
          style={{ ["--draw-len" as string]: "1600", strokeDasharray: 1600, animation: "fv-draw 2.4s ease-out forwards" }}
        />
        {/* Live flowing dashes over the same path */}
        <path
          d="M0,320 L100,300 L200,330 L300,260 L400,290 L500,220 L600,250 L700,180 L800,210 L900,140 L1000,170 L1100,90 L1200,120"
          fill="none"
          stroke="#bfdbfe"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray="6 22"
          className="fv-dash-flow"
          opacity="0.5"
        />
        <circle cx="1100" cy="90" r="5" fill="#bfdbfe" className="fv-glow-pulse" />
      </svg>
      )}

      {/* Candlesticks */}
      {candles && (
        <svg
          className="absolute inset-x-0 bottom-0 h-40 w-full opacity-[0.13]"
          viewBox="0 0 100 80"
          preserveAspectRatio="none"
          aria-hidden
        >
          {CANDLES.map((k, i) => {
            const color = k.up ? UP : DOWN;
            const top = Math.min(k.o, k.c);
            const h = Math.max(2, Math.abs(k.o - k.c));
            return (
              <g key={k.x} className="fv-float" style={{ animationDelay: `${i * 0.35}s`, transformBox: "fill-box" }}>
                <line x1={k.x} y1={k.hi} x2={k.x} y2={k.lo} stroke={color} strokeWidth="0.5" />
                <rect x={k.x - 2} y={top} width="4" height={h} fill={color} />
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}
