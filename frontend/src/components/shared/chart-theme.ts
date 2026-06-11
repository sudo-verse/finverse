/** Shared Recharts styling so every chart matches the terminal theme. */

export const CHART_COLORS = {
  blue: "#3b82f6",
  green: "#10b981",
  amber: "#f59e0b",
  violet: "#8b5cf6",
  rose: "#f43f5e",
  cyan: "#22d3ee",
  slate: "#64748b",
};

export const SIGNAL_COLORS: Record<string, string> = {
  BUY: CHART_COLORS.green,
  SELL: CHART_COLORS.rose,
  HOLD: CHART_COLORS.amber,
};

export const PIE_PALETTE = [
  CHART_COLORS.blue,
  CHART_COLORS.green,
  CHART_COLORS.violet,
  CHART_COLORS.amber,
  CHART_COLORS.cyan,
  CHART_COLORS.rose,
  CHART_COLORS.slate,
];

export const axisStyle = {
  stroke: "rgba(140,165,200,0.25)",
  fontSize: 11,
  tick: { fill: "#8294ab", fontSize: 11 },
  tickLine: false as const,
  axisLine: false as const,
};

export const gridStyle = {
  stroke: "rgba(140,165,200,0.08)",
  vertical: false as const,
};

export const tooltipStyle = {
  contentStyle: {
    background: "#0d1526",
    border: "1px solid rgba(140,165,200,0.18)",
    borderRadius: 10,
    fontSize: 12,
    boxShadow: "0 12px 32px rgba(0,0,0,0.5)",
  },
  labelStyle: { color: "#e6edf7", fontWeight: 600, marginBottom: 4 },
  itemStyle: { padding: 0 },
  cursor: { stroke: "rgba(140,165,200,0.2)" },
};
