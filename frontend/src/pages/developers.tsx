import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Code2,
  Copy,
  KeyRound,
  Terminal,
  TrendingUp,
  Zap,
} from "lucide-react";
import { Footer } from "@/components/layout/footer";
import { Seo } from "@/components/seo";
import { Badge } from "@/components/ui/badge";
import { LEGAL } from "@/lib/legal";
import { cn } from "@/lib/utils";

/**
 * Public, crawlable Developers page — API reference + pricing so external
 * users can evaluate, sign up and buy access to the Finverse API. Standalone
 * chrome (no auth, not inside AppLayout), mirroring the legal pages.
 */

/** Public API base. In prod the frontend talks to VITE_API_URL; fall back to
 *  the deployed gateway so the docs show a working, copy-pasteable URL. */
const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "https://52.66.113.139.sslip.io/api";

const SALES_EMAIL = LEGAL.supportEmail;

// ---------------------------------------------------------------- endpoint catalog
interface Endpoint {
  method: "GET" | "POST";
  path: string;
  desc: string;
}
interface EndpointGroup {
  name: string;
  blurb: string;
  endpoints: Endpoint[];
}

const ENDPOINT_GROUPS: EndpointGroup[] = [
  {
    name: "Conviction & Valuation",
    blurb: "The synthesis layer — composite conviction and relative fair value.",
    endpoints: [
      { method: "GET", path: "/conviction", desc: "Ranked conviction leaderboard with full pillar breakdown." },
      { method: "GET", path: "/conviction/{symbol}", desc: "Single-stock conviction score and the 6 pillars behind it." },
      { method: "GET", path: "/valuation", desc: "Relative fair-value upside for the universe." },
      { method: "GET", path: "/valuation/{symbol}", desc: "Fair value, the P/E & P/B legs and confidence for one stock." },
    ],
  },
  {
    name: "Stock intelligence",
    blurb: "Per-stock fundamentals, technicals and AI-derived analysis.",
    endpoints: [
      { method: "GET", path: "/stocks", desc: "Searchable list of the covered NSE universe." },
      { method: "GET", path: "/stocks/{symbol}/technicals", desc: "RSI, MACD, moving averages and 52-week range position." },
      { method: "GET", path: "/stocks/{symbol}/red-flags", desc: "Surveillance (ASM/GSM), pledge and leverage-stress flags." },
      { method: "GET", path: "/stocks/{symbol}/dcf", desc: "Equity-FCF DCF with bull / base / bear scenarios." },
    ],
  },
  {
    name: "Ownership & insiders",
    blurb: "Who's buying — institutions, promoters and marquee investors.",
    endpoints: [
      { method: "GET", path: "/ownership", desc: "FII / DII quarter-on-quarter shareholding shifts." },
      { method: "GET", path: "/insider/sast", desc: "SAST insider / promoter acquisition & disposal filings." },
      { method: "GET", path: "/superstars", desc: "Portfolios of well-known marquee investors." },
    ],
  },
  {
    name: "Markets & events",
    blurb: "IPOs with GMP, derivatives, dividends and the earnings calendar.",
    endpoints: [
      { method: "GET", path: "/ipos", desc: "Live / upcoming IPOs enriched with grey-market premium." },
      { method: "GET", path: "/fno/oi-buildup", desc: "EOD F&O OI build-up, PCR and max-pain." },
      { method: "GET", path: "/dividends", desc: "Upcoming and recent dividend actions." },
      { method: "GET", path: "/sentiment/{symbol}", desc: "Multi-factor sentiment intelligence score." },
    ],
  },
];

// ---------------------------------------------------------------- pricing
interface Plan {
  name: string;
  price: string;
  cadence?: string;
  tagline: string;
  features: string[];
  cta: { label: string; to?: string; href?: string };
  highlight?: boolean;
}

const PLANS: Plan[] = [
  {
    name: "Developer",
    price: "$0",
    cadence: "/mo",
    tagline: "Build and prototype against the full catalog.",
    features: [
      "All read endpoints",
      "1,000 requests / day",
      "25 AI chat · 5 AI reports / day",
      "Community support",
    ],
    cta: { label: "Get an API key", to: "/settings" },
  },
  {
    name: "Pro",
    price: "$29",
    cadence: "/mo",
    tagline: "Production access with headroom for real apps.",
    features: [
      "Everything in Developer",
      "50,000 requests / day",
      "2,000 AI chat · 500 AI reports / day",
      "Priority email support",
    ],
    cta: { label: "Start Pro", to: "/settings?upgrade=pro" },
    highlight: true,
  },
  {
    name: "Scale",
    price: "$99",
    cadence: "/mo",
    tagline: "High-volume API access for teams.",
    features: [
      "Everything in Pro",
      "250,000 requests / day",
      "10,000 AI chat · 2,500 AI reports / day",
      "Priority support",
    ],
    cta: { label: "Start Scale", to: "/settings?upgrade=scale" },
  },
];

// ---------------------------------------------------------------- helpers
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard?.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="inline-flex items-center gap-1.5 rounded-md border border-border/60 px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground"
      aria-label="Copy to clipboard"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-bull" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function CodeBlock({ title, code }: { title?: string; code: string }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border/60 bg-card/60">
      <div className="flex items-center justify-between border-b border-border/60 bg-secondary/40 px-3 py-2">
        <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Terminal className="h-3.5 w-3.5" /> {title ?? "shell"}
        </span>
        <CopyButton text={code} />
      </div>
      <pre className="overflow-x-auto px-4 py-3 text-[13px] leading-relaxed text-foreground/90">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function SectionTitle({ icon: Icon, children }: { icon: typeof Code2; children: ReactNode }) {
  return (
    <h2 className="flex items-center gap-2 text-xl font-bold tracking-tight">
      <Icon className="h-5 w-5 text-primary" /> {children}
    </h2>
  );
}

const CURL_EXAMPLE = `curl ${API_BASE}/conviction?order=top&limit=10 \\
  -H "Authorization: Bearer YOUR_API_KEY"`;

const JSON_EXAMPLE = `{
  "symbol": "TATASTEEL",
  "name": "Tata Steel Ltd",
  "sector": "Metals & Mining",
  "score": 80.2,
  "verdict": "high conviction",
  "coverage": 6,
  "pillars": [
    { "key": "value",      "label": "Valuation",        "score": 88.4, "signal": "up" },
    { "key": "smart_money","label": "Smart money",      "score": 74.0, "signal": "up" },
    { "key": "momentum",   "label": "Earnings momentum","score": 69.1, "signal": "up" }
  ]
}`;

const METHOD_STYLES: Record<Endpoint["method"], string> = {
  GET: "bg-bull/15 text-bull border-bull/30",
  POST: "bg-blue-500/15 text-blue-400 border-blue-500/30",
};

export default function DevelopersPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Seo
        title="API & Pricing"
        description="The Finverse API — composite conviction scores, fair value, ownership, insider activity, IPO GMP and F&O data for the NSE. Simple REST, JSON, pay-as-you-grow."
      />

      {/* Brand header */}
      <header className="border-b border-border/60">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-4">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-violet-600 text-white shadow">
              <TrendingUp className="h-4 w-4" />
            </div>
            <span className="text-[15px] font-bold tracking-tight">{LEGAL.company}</span>
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <a href="#pricing" className="text-muted-foreground hover:text-foreground">Pricing</a>
            <Link to="/" className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-4 w-4" /> Back to app
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-12">
        {/* Hero */}
        <section className="max-w-2xl">
          <Badge variant="secondary" className="mb-4">REST · JSON · NSE intelligence</Badge>
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            The Finverse API
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Ship the same composite conviction scores, fair value, smart-money flows, insider
            activity, IPO grey-market premiums and F&amp;O analytics that power Finverse — over a
            clean REST API. One token, JSON everywhere, pay as you grow.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/settings"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow transition-colors hover:bg-primary/90"
            >
              Get an API key <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href={`${API_BASE.replace(/\/api$/, "")}/docs`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-border/60 px-5 py-2.5 text-sm font-semibold transition-colors hover:bg-accent/60"
            >
              <Code2 className="h-4 w-4" /> Interactive reference
            </a>
          </div>
        </section>

        {/* Quick start */}
        <section className="mt-16 space-y-5">
          <SectionTitle icon={Zap}>Quick start</SectionTitle>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Every request goes to the base URL below and authenticates with a bearer token. Generate
            a key from your account, then call any endpoint:
          </p>
          <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border/60 bg-secondary/40 px-3 py-2 text-sm">
            <KeyRound className="h-4 w-4 text-muted-foreground" />
            <span className="font-mono text-foreground/90">{API_BASE}</span>
            <span className="ml-auto"><CopyButton text={API_BASE} /></span>
          </div>
          <CodeBlock title="curl" code={CURL_EXAMPLE} />
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Example response</p>
            <CodeBlock title="200 OK · application/json" code={JSON_EXAMPLE} />
          </div>
        </section>

        {/* Endpoint catalog */}
        <section className="mt-16 space-y-6">
          <SectionTitle icon={Code2}>Endpoints</SectionTitle>
          <p className="max-w-2xl text-sm text-muted-foreground">
            A representative slice of the catalog. The full, always-current reference — with every
            parameter and schema — lives in the{" "}
            <a
              href={`${API_BASE.replace(/\/api$/, "")}/docs`}
              target="_blank"
              rel="noreferrer"
              className="text-primary hover:underline"
            >
              interactive OpenAPI docs
            </a>
            .
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            {ENDPOINT_GROUPS.map((g) => (
              <div key={g.name} className="rounded-xl border border-border/60 bg-card/40 p-5">
                <h3 className="text-sm font-semibold">{g.name}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{g.blurb}</p>
                <ul className="mt-4 space-y-3">
                  {g.endpoints.map((e) => (
                    <li key={e.path} className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "rounded border px-1.5 py-0.5 font-mono text-[10px] font-bold",
                            METHOD_STYLES[e.method],
                          )}
                        >
                          {e.method}
                        </span>
                        <code className="text-[13px] text-foreground/90">{e.path}</code>
                      </div>
                      <p className="pl-1 text-xs text-muted-foreground">{e.desc}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="mt-20 scroll-mt-20 space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight">Simple, usage-based pricing</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Start free. Upgrade when you ship. Cancel anytime.
            </p>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {PLANS.map((p) => (
              <div
                key={p.name}
                className={cn(
                  "relative flex flex-col rounded-2xl border p-6",
                  p.highlight
                    ? "border-primary/50 bg-primary/[0.04] shadow-lg shadow-primary/10"
                    : "border-border/60 bg-card/40",
                )}
              >
                {p.highlight && (
                  <span className="absolute -top-3 left-6 rounded-full bg-primary px-3 py-0.5 text-[11px] font-semibold text-primary-foreground">
                    Most popular
                  </span>
                )}
                <h3 className="text-lg font-semibold">{p.name}</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-3xl font-bold tracking-tight">{p.price}</span>
                  {p.cadence && <span className="text-sm text-muted-foreground">{p.cadence}</span>}
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{p.tagline}</p>
                <ul className="mt-5 flex-1 space-y-2.5">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-bull" />
                      <span className="text-foreground/90">{f}</span>
                    </li>
                  ))}
                </ul>
                {p.cta.to ? (
                  <Link
                    to={p.cta.to}
                    className={cn(
                      "mt-6 inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors",
                      p.highlight
                        ? "bg-primary text-primary-foreground hover:bg-primary/90"
                        : "border border-border/60 hover:bg-accent/60",
                    )}
                  >
                    {p.cta.label}
                  </Link>
                ) : (
                  <a
                    href={p.cta.href}
                    className="mt-6 inline-flex items-center justify-center gap-2 rounded-lg border border-border/60 px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-accent/60"
                  >
                    {p.cta.label}
                  </a>
                )}
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-muted-foreground">
            Prices in USD, billed monthly. Daily limits reset at 00:00 UTC. Need something in
            between?{" "}
            <a href={`mailto:${SALES_EMAIL}`} className="text-primary hover:underline">
              Talk to us
            </a>
            .
          </p>
        </section>

        {/* FAQ */}
        <section className="mt-20 space-y-5">
          <h2 className="text-2xl font-bold tracking-tight">FAQ</h2>
          <div className="grid gap-5 md:grid-cols-2">
            {[
              {
                q: "How do I authenticate?",
                a: "Pass your token as a bearer header: Authorization: Bearer YOUR_API_KEY. Generate and rotate keys from your account settings.",
              },
              {
                q: "What data do you cover?",
                a: "The listed NSE equity universe — fundamentals, technicals, shareholding, insider/SAST filings, IPOs with GMP, EOD F&O, dividends and AI-derived analysis.",
              },
              {
                q: "How fresh is the data?",
                a: "Market and corporate feeds refresh through the trading day; derivatives use the EOD bhavcopy. Each response carries the as-of timestamp.",
              },
              {
                q: "Is this investment advice?",
                a: "No. Finverse is informational and educational only — not a SEBI-registered adviser. See our Disclaimer.",
              },
            ].map((f) => (
              <div key={f.q} className="rounded-xl border border-border/60 bg-card/40 p-5">
                <h3 className="text-sm font-semibold">{f.q}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.a}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
