import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, Code2, Copy, KeyRound, Terminal, Zap } from "lucide-react";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { Seo } from "@/components/seo";
import { cn } from "@/lib/utils";

/** Public, crawlable Developers page — API reference + pricing. Light, premium
 *  chrome shared with the landing page; dark code panels for contrast. */

const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "https://52.66.113.139.sslip.io/api";

const DOCS_URL = `${API_BASE.replace(/\/api$/, "")}/docs`;
const SALES_EMAIL = "support@finverse.app";

// ---------------------------------------------------------------- endpoint catalog
interface Endpoint {
  method: "GET" | "POST";
  path: string;
  desc: string;
}
const ENDPOINT_GROUPS: { name: string; blurb: string; endpoints: Endpoint[] }[] = [
  {
    name: "Conviction & Valuation",
    blurb: "The synthesis layer — composite conviction and relative fair value.",
    endpoints: [
      { method: "GET", path: "/conviction", desc: "Ranked conviction leaderboard with the full pillar breakdown." },
      { method: "GET", path: "/conviction/{symbol}", desc: "Single-stock conviction score and the six pillars behind it." },
      { method: "GET", path: "/valuation/{symbol}", desc: "Fair value, the P/E & P/B legs and confidence for one stock." },
    ],
  },
  {
    name: "Stock intelligence",
    blurb: "Per-stock fundamentals, technicals and AI-derived analysis.",
    endpoints: [
      { method: "GET", path: "/stocks", desc: "Searchable list of the covered NSE universe." },
      { method: "GET", path: "/stocks/{symbol}/technicals", desc: "RSI, MACD, moving averages and 52-week position." },
      { method: "GET", path: "/stocks/{symbol}/dcf", desc: "Equity-FCF DCF with bull / base / bear scenarios." },
    ],
  },
  {
    name: "Ownership & insiders",
    blurb: "Who's buying — institutions, promoters and marquee investors.",
    endpoints: [
      { method: "GET", path: "/ownership", desc: "FII / DII quarter-on-quarter shareholding shifts." },
      { method: "GET", path: "/insider/sast", desc: "SAST insider & promoter acquisition / disposal filings." },
      { method: "GET", path: "/superstars", desc: "Portfolios of well-known marquee investors." },
    ],
  },
  {
    name: "Markets & events",
    blurb: "IPOs with GMP, derivatives, dividends and sentiment.",
    endpoints: [
      { method: "GET", path: "/ipos", desc: "Live / upcoming IPOs enriched with grey-market premium." },
      { method: "GET", path: "/fno/oi-buildup", desc: "EOD F&O OI build-up, PCR and max-pain." },
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
    features: ["All read endpoints", "1,000 requests / day", "5 req/sec burst", "25 AI chat · 5 AI reports / day"],
    cta: { label: "Get an API key", to: "/settings" },
  },
  {
    name: "Pro",
    price: "$29",
    cadence: "/mo",
    tagline: "Production access with headroom for real apps.",
    features: ["Everything in Developer", "50,000 requests / day", "20 req/sec burst", "2,000 AI chat · 500 reports / day"],
    cta: { label: "Start Pro", to: "/settings?upgrade=pro" },
    highlight: true,
  },
  {
    name: "Scale",
    price: "$99",
    cadence: "/mo",
    tagline: "High-volume API access for teams.",
    features: ["Everything in Pro", "250,000 requests / day", "50 req/sec burst", "Priority support"],
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
      className="inline-flex items-center gap-1.5 rounded-md border border-white/15 px-2 py-1 text-xs text-zinc-400 transition-colors hover:bg-white/5 hover:text-zinc-200"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function CodeBlock({ title, code }: { title?: string; code: string }) {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 bg-[#0b1220] shadow-sm">
      <div className="flex items-center justify-between border-b border-white/10 px-3 py-2">
        <span className="flex items-center gap-2 text-xs font-medium text-zinc-400">
          <Terminal className="h-3.5 w-3.5" /> {title ?? "shell"}
        </span>
        <CopyButton text={code} />
      </div>
      <pre className="overflow-x-auto px-4 py-3 text-[13px] leading-relaxed text-zinc-200">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function SectionTitle({ icon: Icon, children }: { icon: typeof Code2; children: ReactNode }) {
  return (
    <h2 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-zinc-900">
      <Icon className="h-5 w-5 text-blue-600" /> {children}
    </h2>
  );
}

const CURL_EXAMPLE = `curl ${API_BASE}/conviction?order=top&limit=10 \\
  -H "Authorization: Bearer YOUR_API_KEY"`;

const JSON_EXAMPLE = `{
  "symbol": "TATASTEEL",
  "name": "Tata Steel Ltd",
  "score": 80.2,
  "verdict": "high conviction",
  "coverage": 6,
  "pillars": [
    { "key": "value",       "label": "Valuation",         "score": 88.4 },
    { "key": "smart_money", "label": "Smart money",       "score": 74.0 },
    { "key": "momentum",    "label": "Earnings momentum", "score": 69.1 }
  ]
}`;

const METHOD_STYLES: Record<Endpoint["method"], string> = {
  GET: "bg-emerald-50 text-emerald-700 border-emerald-200",
  POST: "bg-blue-50 text-blue-700 border-blue-200",
};

export default function DevelopersPage() {
  return (
    <div className="min-h-screen bg-white text-zinc-900">
      <Seo
        title="API & Pricing"
        description="The Finverse API — composite conviction scores, fair value, ownership, insider activity, IPO GMP and F&O data for the NSE. Simple REST, JSON, pay-as-you-grow."
      />
      <SiteHeader />

      <main className="mx-auto w-full max-w-6xl px-6">
        {/* Hero */}
        <section className="max-w-2xl py-16 md:py-20">
          <span className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs font-medium text-zinc-600">
            REST · JSON · NSE intelligence
          </span>
          <h1 className="mt-5 text-4xl font-bold tracking-tight text-zinc-900 sm:text-5xl">The Finverse API</h1>
          <p className="mt-5 text-lg leading-relaxed text-zinc-600">
            Ship the same conviction scores, fair value, smart-money flows, insider activity, IPO grey-market
            premiums and F&amp;O analytics that power Finverse — over a clean REST API. One token, JSON
            everywhere, pay as you grow.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/settings" className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-zinc-800">
              Get an API key <ArrowRight className="h-4 w-4" />
            </Link>
            <a href={DOCS_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 px-5 py-3 text-sm font-semibold text-zinc-800 transition-colors hover:bg-zinc-50">
              <Code2 className="h-4 w-4" /> Interactive reference
            </a>
          </div>
        </section>

        {/* Quick start */}
        <section className="space-y-5 border-t border-zinc-200 py-16">
          <SectionTitle icon={Zap}>Quick start</SectionTitle>
          <p className="max-w-2xl text-zinc-600">
            Every request goes to the base URL below and authenticates with a bearer token. Generate a scoped
            key from your settings, then call any endpoint:
          </p>
          <div className="flex flex-wrap items-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm">
            <KeyRound className="h-4 w-4 text-zinc-500" />
            <span className="font-mono text-zinc-800">{API_BASE}</span>
          </div>
          <CodeBlock title="curl" code={CURL_EXAMPLE} />
          <p className="text-sm font-medium text-zinc-500">Example response</p>
          <CodeBlock title="200 OK · application/json" code={JSON_EXAMPLE} />
        </section>

        {/* Endpoints */}
        <section className="space-y-6 border-t border-zinc-200 py-16">
          <SectionTitle icon={Code2}>Endpoints</SectionTitle>
          <p className="max-w-2xl text-zinc-600">
            A representative slice of the catalog. The full, always-current reference lives in the{" "}
            <a href={DOCS_URL} target="_blank" rel="noreferrer" className="font-medium text-blue-600 hover:underline">
              interactive OpenAPI docs
            </a>.
          </p>
          <div className="grid gap-5 md:grid-cols-2">
            {ENDPOINT_GROUPS.map((g) => (
              <div key={g.name} className="rounded-2xl border border-zinc-200 bg-white p-6">
                <h3 className="text-sm font-semibold text-zinc-900">{g.name}</h3>
                <p className="mt-1 text-xs text-zinc-500">{g.blurb}</p>
                <ul className="mt-5 space-y-3.5">
                  {g.endpoints.map((e) => (
                    <li key={e.path} className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={cn("rounded border px-1.5 py-0.5 font-mono text-[10px] font-bold", METHOD_STYLES[e.method])}>
                          {e.method}
                        </span>
                        <code className="text-[13px] text-zinc-800">{e.path}</code>
                      </div>
                      <p className="text-xs text-zinc-500">{e.desc}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="scroll-mt-20 space-y-8 border-t border-zinc-200 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-zinc-900">Simple, usage-based pricing</h2>
            <p className="mt-3 text-zinc-600">Start free. Upgrade when you ship. Cancel anytime.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {PLANS.map((p) => (
              <div
                key={p.name}
                className={cn(
                  "relative flex flex-col rounded-2xl border p-7",
                  p.highlight ? "border-zinc-900 shadow-xl" : "border-zinc-200",
                )}
              >
                {p.highlight && (
                  <span className="absolute -top-3 left-7 rounded-full bg-zinc-900 px-3 py-0.5 text-[11px] font-semibold text-white">
                    Most popular
                  </span>
                )}
                <h3 className="text-lg font-semibold text-zinc-900">{p.name}</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-4xl font-bold tracking-tight text-zinc-900">{p.price}</span>
                  {p.cadence && <span className="text-sm text-zinc-500">{p.cadence}</span>}
                </div>
                <p className="mt-2 text-sm text-zinc-500">{p.tagline}</p>
                <ul className="mt-6 flex-1 space-y-3">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm text-zinc-700">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to={p.cta.to ?? "/settings"}
                  className={cn(
                    "mt-7 inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors",
                    p.highlight ? "bg-zinc-900 text-white hover:bg-zinc-800" : "border border-zinc-300 text-zinc-800 hover:bg-zinc-50",
                  )}
                >
                  {p.cta.label}
                </Link>
              </div>
            ))}
          </div>
          <p className="text-center text-sm text-zinc-500">
            Prices in USD, billed monthly. Need higher volume or an SLA?{" "}
            <a href={`mailto:${SALES_EMAIL}`} className="font-medium text-blue-600 hover:underline">Contact sales</a>.
          </p>
        </section>

        {/* FAQ */}
        <section className="space-y-6 border-t border-zinc-200 py-16">
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900">FAQ</h2>
          <div className="grid gap-5 md:grid-cols-2">
            {[
              { q: "How do I authenticate?", a: "Pass your token as a bearer header: Authorization: Bearer YOUR_API_KEY. Generate, scope (read / ai / write) and rotate keys from your settings." },
              { q: "What are the rate limits?", a: "Two layers: a daily quota (Developer 1k, Pro 50k, Scale 250k) and a per-second burst cap (5 / 20 / 50). Exceeding either returns 429 with a Retry-After header." },
              { q: "What data do you cover?", a: "The listed NSE equity universe — fundamentals, technicals, shareholding, insider/SAST filings, IPOs with GMP, EOD F&O, dividends and AI analysis." },
              { q: "Is this investment advice?", a: "No. Finverse is informational and educational only — not a SEBI-registered adviser. See our Disclaimer." },
            ].map((f) => (
              <div key={f.q} className="rounded-2xl border border-zinc-200 bg-white p-6">
                <h3 className="text-sm font-semibold text-zinc-900">{f.q}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-600">{f.a}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
