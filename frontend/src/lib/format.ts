/** Formatting helpers for Indian market conventions. */

const inrFull = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const inrCompactNum = new Intl.NumberFormat("en-IN", {
  maximumFractionDigits: 2,
});

export function formatINR(value: number): string {
  return inrFull.format(value);
}

/** Formats large values using Indian units: ₹1.2L Cr, ₹450 Cr, ₹3.4 L, etc. */
export function formatINRCompact(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1e12) return `${sign}₹${inrCompactNum.format(abs / 1e12)}L Cr`;
  if (abs >= 1e7) return `${sign}₹${inrCompactNum.format(abs / 1e7)} Cr`;
  if (abs >= 1e5) return `${sign}₹${inrCompactNum.format(abs / 1e5)} L`;
  if (abs >= 1e3) return `${sign}₹${inrCompactNum.format(abs / 1e3)}K`;
  return `${sign}₹${inrCompactNum.format(abs)}`;
}

export function formatNumber(value: number, digits = 2): string {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatPercent(value: number, digits = 2): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

/** The API returns ratios as fractions (0.046 = 4.6%). */
export function formatFraction(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return "—";
  return formatPercent(value * 100, digits);
}

/** Null-safe number with fallback dash. */
export function formatMaybe(value: number | null | undefined, digits = 2, suffix = ""): string {
  if (value === null || value === undefined) return "—";
  return `${formatNumber(value, digits)}${suffix}`;
}

/** NSE financial results report monetary values in ₹ Lakhs (1 Lakh = 1e5). */
export function formatLakhs(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return formatINRCompact(value * 1e5);
}

/** Some news sources (Google News RSS) ship raw HTML in headlines — and the
 *  DB column truncation can cut a tag mid-attribute, so handle unterminated
 *  tags and naked URLs too. */
export function stripHtml(text: string | null | undefined): string {
  if (!text) return "";
  return text
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/<[^>]*>/g, " ") // complete tags
    .replace(/<[^>]*$/, " ") // tag cut off by truncation
    .replace(/https?:\/\/\S+/g, " ") // leftover URLs are noise in a headline
    .replace(/&nbsp;|&amp;|&quot;|&#39;/g, (m) =>
      m === "&amp;" ? "&" : m === "&quot;" ? '"' : m === "&#39;" ? "'" : " ",
    )
    .replace(/\s+/g, " ")
    .trim();
}

export function formatCompact(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

/** All date display is pinned to IST — this is an NSE app, and the backend
 *  now serializes timestamps with an explicit UTC offset. */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false, // en-IN defaults to 12h *without* am/pm — ambiguous
    timeZone: "Asia/Kolkata",
  });
}

export function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(iso);
}
