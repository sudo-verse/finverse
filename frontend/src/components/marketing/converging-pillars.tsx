const PILLARS = [
  { label: "Valuation", x: 60 },
  { label: "Momentum", x: 164 },
  { label: "Smart money", x: 268 },
  { label: "Insider", x: 372 },
  { label: "Technical", x: 476 },
  { label: "Sentiment", x: 580 },
];

const CX = 320;
const CY = 320;

/**
 * Animated hero visual: the six conviction pillars at the top, their lines
 * curving down and converging into a single glowing Conviction node — our
 * on-brand answer to langchain's converging-arc animation.
 */
export function ConvergingPillars() {
  return (
    <svg viewBox="0 0 640 380" className="h-full w-full" aria-label="Six pillars converging into one conviction score">
      <defs>
        <linearGradient id="cp-line" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#60a5fa" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#93c5fd" stopOpacity="0.9" />
        </linearGradient>
        <radialGradient id="cp-node" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#1e3a8a" />
        </radialGradient>
      </defs>

      {/* Converging curves */}
      {PILLARS.map((p, i) => {
        const d = `M${p.x},56 C${p.x},190 ${CX},190 ${CX},${CY - 8}`;
        return (
          <g key={p.label}>
            <path
              d={d}
              fill="none"
              stroke="url(#cp-line)"
              strokeWidth="1.5"
              style={{
                ["--draw-len" as string]: "560",
                strokeDasharray: 560,
                animation: `fv-draw 1.8s cubic-bezier(0.22,1,0.36,1) ${0.18 * i}s forwards`,
              }}
            />
            <path
              d={d}
              fill="none"
              stroke="#bfdbfe"
              strokeWidth="1.25"
              strokeDasharray="2 20"
              className="fv-dash-flow"
              opacity="0.24"
            />
          </g>
        );
      })}

      {/* Pillar chips */}
      {PILLARS.map((p) => (
        <g key={`chip-${p.label}`}>
          <rect
            x={p.x - 48}
            y={28}
            width={96}
            height={26}
            rx={13}
            fill="#0f1830"
            stroke="rgba(147,197,253,0.25)"
          />
          <text x={p.x} y={45} textAnchor="middle" fontSize="11" fill="#cbd5e1" fontWeight="500">
            {p.label}
          </text>
        </g>
      ))}

      {/* Conviction node */}
      <circle cx={CX} cy={CY} r="46" fill="#3b82f6" opacity="0.18" className="fv-glow-pulse" />
      <circle cx={CX} cy={CY} r="34" fill="url(#cp-node)" stroke="rgba(147,197,253,0.5)" strokeWidth="1" />
      <text x={CX} y={CY - 2} textAnchor="middle" fontSize="24" fontWeight="700" fill="#ffffff">
        80
      </text>
      <text x={CX} y={CY + 14} textAnchor="middle" fontSize="8.5" letterSpacing="1.5" fill="#bfdbfe">
        CONVICTION
      </text>
    </svg>
  );
}
