import { Link } from "react-router-dom";
import {
  ArrowRight,
  CandlestickChart,
  Check,
  Gauge,
  Landmark,
  Layers,
  Rocket,
  Scale,
  Target,
  UserCheck,
} from "lucide-react";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { Seo } from "@/components/seo";

const FEATURES = [
  { icon: Target, name: "Conviction Score", desc: "One 0–100 score synthesising six independent pillars — so the headline number is always explainable." },
  { icon: Scale, name: "Fair Value", desc: "Relative valuation and DCF upside with the P/E and P/B legs broken out, not a black box." },
  { icon: Landmark, name: "Smart Money", desc: "Quarter-on-quarter FII & DII shifts — see where institutional capital is actually moving." },
  { icon: UserCheck, name: "Insider & SAST", desc: "Promoter and insider acquisitions vs disposals, weighted by skin in the game." },
  { icon: CandlestickChart, name: "Technicals", desc: "RSI, MACD, moving averages, pivots and 52-week position — computed across the universe." },
  { icon: Gauge, name: "Sentiment", desc: "Multi-factor sentiment intelligence blending news, momentum and market mood." },
  { icon: Rocket, name: "IPO tracker + GMP", desc: "Live and upcoming IPOs enriched with grey-market premium and subscription data." },
  { icon: Layers, name: "F&O analytics", desc: "OI build-up, PCR and max-pain from the EOD derivatives book." },
];

const PILLARS = ["Valuation", "Earnings momentum", "Smart money", "Insider / SAST", "52-week trend", "Sentiment"];

/** A faux dark product panel — shows the terminal's flavour inside the light
 *  marketing page (the striking contrast langchain gets from real screenshots). */
function ProductPreview() {
  const rows = [
    { sym: "TATASTEEL", name: "Tata Steel", score: 80, verdict: "High conviction" },
    { sym: "ICICIBANK", name: "ICICI Bank", score: 74, verdict: "Constructive" },
    { sym: "INFY", name: "Infosys", score: 67, verdict: "Constructive" },
    { sym: "RELIANCE", name: "Reliance Ind.", score: 61, verdict: "Neutral" },
    { sym: "HINDUNILVR", name: "Hindustan Uni.", score: 48, verdict: "Neutral" },
  ];
  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-[#0b1220] shadow-2xl shadow-zinc-900/20 ring-1 ring-zinc-900/5">
      <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-[#f43f5e]/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#f59e0b]/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#10b981]/70" />
        <span className="ml-3 text-xs font-medium text-zinc-400">Conviction leaderboard</span>
      </div>
      <div className="divide-y divide-white/5">
        {rows.map((r) => (
          <div key={r.sym} className="flex items-center gap-4 px-4 py-3">
            <div className="w-28 min-w-0">
              <div className="truncate text-sm font-semibold text-zinc-100">{r.sym}</div>
              <div className="truncate text-[11px] text-zinc-500">{r.name}</div>
            </div>
            <div className="flex-1">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${r.score}%`,
                    background: r.score >= 68 ? "#10b981" : r.score >= 56 ? "#3b82f6" : "#f59e0b",
                  }}
                />
              </div>
            </div>
            <div className="w-10 text-right text-sm font-semibold tabular-nums text-zinc-100">{r.score}</div>
            <div className="hidden w-32 text-right text-[11px] font-medium text-zinc-400 sm:block">{r.verdict}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-zinc-900">
      <Seo
        title="AI Stock Intelligence for the NSE"
        description="Finverse turns NSE market data into one explainable conviction score — valuation, smart money, insider activity, technicals and sentiment, over a clean API."
      />
      <SiteHeader />

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="mx-auto grid w-full max-w-6xl items-center gap-12 px-6 py-20 md:py-28 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs font-medium text-zinc-600">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Built for the Indian markets
            </span>
            <h1 className="mt-5 text-4xl font-bold leading-[1.08] tracking-tight text-zinc-900 sm:text-5xl lg:text-6xl">
              Equity research,<br />
              <span className="text-zinc-400">distilled to one</span><br />
              explainable score.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-zinc-600">
              Finverse synthesises valuation, smart-money flows, insider activity, technicals and sentiment
              across the NSE universe — into a single conviction score you can actually defend. Use the app,
              or build on the API.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
              >
                Start free <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/developers"
                className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-5 py-3 text-sm font-semibold text-zinc-800 transition-colors hover:bg-zinc-50"
              >
                Explore the API
              </Link>
            </div>
            <p className="mt-5 text-sm text-zinc-500">No card required · Free tier · Cancel anytime</p>
          </div>

          <div className="relative">
            <div className="pointer-events-none absolute -inset-8 -z-10 rounded-full bg-blue-500/5 blur-3xl" />
            <ProductPreview />
          </div>
        </div>
      </section>

      {/* Coverage strip */}
      <section className="border-y border-zinc-200 bg-zinc-50">
        <div className="mx-auto grid w-full max-w-6xl grid-cols-2 gap-px overflow-hidden px-6 py-12 sm:grid-cols-4">
          {[
            ["2,300+", "NSE stocks covered"],
            ["6", "scoring pillars"],
            ["40+", "data & analytics views"],
            ["1 API", "for all of it"],
          ].map(([stat, label]) => (
            <div key={label} className="text-center">
              <div className="text-3xl font-bold tracking-tight text-zinc-900">{stat}</div>
              <div className="mt-1 text-sm text-zinc-500">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto w-full max-w-6xl scroll-mt-20 px-6 py-20 md:py-28">
        <div className="max-w-2xl">
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
            Every angle on a stock, in one place
          </h2>
          <p className="mt-4 text-lg text-zinc-600">
            Not another chart tool. Finverse computes the hard signals — and shows its work on every one.
          </p>
        </div>
        <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-zinc-200 bg-zinc-200 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div key={f.name} className="group bg-white p-7 transition-colors hover:bg-zinc-50">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-900 text-white">
                <f.icon className="h-5 w-5" />
              </span>
              <h3 className="mt-5 text-base font-semibold text-zinc-900">{f.name}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Synthesis section */}
      <section className="border-y border-zinc-200 bg-zinc-50">
        <div className="mx-auto grid w-full max-w-6xl items-center gap-12 px-6 py-20 md:py-28 lg:grid-cols-2">
          <div>
            <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">The synthesis layer</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
              A score you can defend in a meeting
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-zinc-600">
              Most tools give you a number and ask for your trust. Finverse blends six independent pillars,
              renormalises over whatever data each stock has, and reports the full breakdown — so you always
              know <em>why</em> it's an 80 and not a 50.
            </p>
            <Link to="/login" className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-zinc-900 hover:gap-3 transition-all">
              See it on a live stock <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="space-y-4">
              {PILLARS.map((p, i) => {
                const score = [88, 71, 74, 62, 58, 50][i];
                return (
                  <div key={p} className="flex items-center gap-4">
                    <div className="w-36 text-sm font-medium text-zinc-700">{p}</div>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-100">
                      <div className="h-full rounded-full bg-zinc-900" style={{ width: `${score}%` }} />
                    </div>
                    <div className="w-8 text-right text-sm font-semibold tabular-nums text-zinc-900">{score}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* API band */}
      <section className="mx-auto w-full max-w-6xl px-6 py-20 md:py-28">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Developer-first</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
              Build on the same data
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-zinc-600">
              Every signal in the app is one REST call away. Scoped API keys, per-second and daily rate
              limits, and usage-based pricing that starts free.
            </p>
            <ul className="mt-6 space-y-3">
              {["Bearer-token auth with read / ai / write scopes", "Clean JSON, camelCase, OpenAPI reference", "Free tier — upgrade only when you ship"].map((t) => (
                <li key={t} className="flex items-start gap-2.5 text-sm text-zinc-700">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> {t}
                </li>
              ))}
            </ul>
            <Link to="/developers" className="mt-8 inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-zinc-800">
              Read the API docs <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-[#0b1220] shadow-xl">
            <div className="border-b border-white/10 px-4 py-2.5 text-xs font-medium text-zinc-400">curl</div>
            <pre className="overflow-x-auto px-5 py-5 text-[13px] leading-relaxed text-zinc-200">
              <code>{`curl https://api.finverse.app/conviction \\
  -H "Authorization: Bearer fv_live_…"

{
  "symbol": "TATASTEEL",
  "score": 80.2,
  "verdict": "high conviction",
  "pillars": [ … ]
}`}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="px-6 pb-24">
        <div className="mx-auto w-full max-w-6xl overflow-hidden rounded-3xl bg-zinc-900 px-8 py-16 text-center md:py-20">
          <h2 className="mx-auto max-w-2xl text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Stop guessing. Start with conviction.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-zinc-400">
            Free to start. Open the app or build on the API in minutes.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link to="/login" className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-200">
              Get started free <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/developers" className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10">
              View pricing
            </Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
