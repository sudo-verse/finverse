import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
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
import { AnimatedBackground } from "@/components/marketing/animated-background";
import { ConvergingPillars } from "@/components/marketing/converging-pillars";
import { Seo } from "@/components/seo";

const FEATURES = [
  { icon: Target, name: "Conviction Score", desc: "One 0–100 score synthesising six independent pillars — always explainable." },
  { icon: Scale, name: "Fair Value", desc: "Relative valuation and DCF upside with the P/E and P/B legs broken out." },
  { icon: Landmark, name: "Smart Money", desc: "Quarter-on-quarter FII & DII shifts — see where institutional capital moves." },
  { icon: UserCheck, name: "Insider & SAST", desc: "Promoter and insider acquisitions vs disposals, weighted by skin in the game." },
  { icon: CandlestickChart, name: "Technicals", desc: "RSI, MACD, moving averages, pivots and 52-week position across the universe." },
  { icon: Gauge, name: "Sentiment", desc: "Multi-factor sentiment blending news, momentum and market mood." },
  { icon: Rocket, name: "IPO tracker + GMP", desc: "Live and upcoming IPOs enriched with grey-market premium and subscription." },
  { icon: Layers, name: "F&O analytics", desc: "OI build-up, PCR and max-pain from the EOD derivatives book." },
];

const PILLARS = ["Valuation", "Earnings momentum", "Smart money", "Insider / SAST", "52-week trend", "Sentiment"];

/** Fade-and-rise on scroll into view. */
function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.75, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#060a13] text-white">
      <Seo
        title="AI Stock Intelligence for the NSE"
        description="Finverse turns NSE market data into one explainable conviction score — valuation, smart money, insider activity, technicals and sentiment, over a clean API."
      />
      <SiteHeader />

      {/* Hero */}
      <section className="relative isolate overflow-hidden">
        <AnimatedBackground priceLine={false} candles={false} />
        <div className="mx-auto w-full max-w-4xl px-6 pb-8 pt-20 text-center md:pt-28">
          <motion.span
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-zinc-300"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 fv-pulse" /> Built for the Indian markets
          </motion.span>
          <motion.h1
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.05 }}
            className="mx-auto mt-6 max-w-3xl text-4xl font-bold leading-[1.08] tracking-tight text-white sm:text-5xl lg:text-6xl"
          >
            Six market signals.<br />
            <span className="text-glow text-blue-300">One conviction score.</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-zinc-400"
          >
            Finverse fuses valuation, smart-money flows, insider activity, technicals and sentiment across the
            NSE universe — into a single score you can defend. Use the app, or build on the API.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25 }}
            className="mt-8 flex flex-wrap items-center justify-center gap-3"
          >
            <Link to="/login" className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-200">
              Start free <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/developers" className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/5">
              Explore the API
            </Link>
          </motion.div>
        </div>

        {/* Converging pillars → conviction node */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="relative mx-auto h-[300px] w-full max-w-3xl px-6 sm:h-[360px]"
        >
          <ConvergingPillars />
        </motion.div>
      </section>

      {/* Coverage strip */}
      <section className="border-y border-white/10 bg-white/[0.02]">
        <div className="mx-auto grid w-full max-w-6xl grid-cols-2 gap-y-8 px-6 py-14 sm:grid-cols-4">
          {[
            ["2,300+", "NSE stocks covered"],
            ["6", "scoring pillars"],
            ["40+", "data & analytics views"],
            ["1 API", "for all of it"],
          ].map(([stat, label], i) => (
            <Reveal key={label} delay={i * 0.05} className="text-center">
              <div className="text-3xl font-bold tracking-tight text-white">{stat}</div>
              <div className="mt-1 text-sm text-zinc-500">{label}</div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto w-full max-w-6xl scroll-mt-20 px-6 py-24">
        <Reveal className="max-w-2xl">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Every angle on a stock, in one place
          </h2>
          <p className="mt-4 text-lg text-zinc-400">
            Not another chart tool. Finverse computes the hard signals — and shows its work on every one.
          </p>
        </Reveal>
        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f, i) => (
            <Reveal key={f.name} delay={(i % 4) * 0.04}>
              <div className="group h-full rounded-2xl border border-white/10 bg-white/[0.03] p-6 transition-colors hover:border-blue-500/40 hover:bg-white/[0.05]">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600/15 text-blue-400 ring-1 ring-blue-500/20">
                  <f.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-5 text-base font-semibold text-white">{f.name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-400">{f.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Synthesis */}
      <section className="border-y border-white/10 bg-white/[0.02]">
        <div className="mx-auto grid w-full max-w-6xl items-center gap-12 px-6 py-24 lg:grid-cols-2">
          <Reveal>
            <span className="text-sm font-semibold uppercase tracking-wider text-blue-400">The synthesis layer</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              A score you can defend in a meeting
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-zinc-400">
              Most tools give you a number and ask for your trust. Finverse blends six independent pillars,
              renormalises over whatever data each stock has, and reports the full breakdown — so you always
              know <em>why</em> it's an 80 and not a 50.
            </p>
            <Link to="/login" className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-white transition-all hover:gap-3">
              See it on a live stock <ArrowRight className="h-4 w-4" />
            </Link>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="rounded-2xl border border-white/10 bg-[#0b1220] p-6">
              <div className="space-y-4">
                {PILLARS.map((p, i) => {
                  const score = [88, 71, 74, 62, 58, 50][i];
                  return (
                    <div key={p} className="flex items-center gap-4">
                      <div className="w-36 text-sm font-medium text-zinc-300">{p}</div>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
                        <motion.div
                          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-400"
                          initial={{ width: 0 }}
                          whileInView={{ width: `${score}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.9, delay: 0.1 + i * 0.08, ease: "easeOut" }}
                        />
                      </div>
                      <div className="w-8 text-right text-sm font-semibold tabular-nums text-white">{score}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* API band */}
      <section className="mx-auto w-full max-w-6xl px-6 py-24">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <Reveal>
            <span className="text-sm font-semibold uppercase tracking-wider text-blue-400">Developer-first</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">Build on the same data</h2>
            <p className="mt-4 text-lg leading-relaxed text-zinc-400">
              Every signal in the app is one REST call away. Scoped API keys, per-second and daily rate
              limits, and usage-based pricing that starts free.
            </p>
            <ul className="mt-6 space-y-3">
              {["Bearer-token auth with read / ai / write scopes", "Clean JSON, camelCase, OpenAPI reference", "Free tier — upgrade only when you ship"].map((t) => (
                <li key={t} className="flex items-start gap-2.5 text-sm text-zinc-300">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" /> {t}
                </li>
              ))}
            </ul>
            <Link to="/developers" className="mt-8 inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-200">
              Read the API docs <ArrowRight className="h-4 w-4" />
            </Link>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-[#0b1220] shadow-xl">
              <div className="flex items-center gap-2 border-b border-white/10 px-4 py-2.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#f43f5e]/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-[#f59e0b]/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-[#10b981]/70" />
                <span className="ml-2 text-xs font-medium text-zinc-500">curl</span>
              </div>
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
          </Reveal>
        </div>
      </section>

      {/* Final CTA over animated chart */}
      <section className="px-6 pb-24">
        <div className="relative isolate mx-auto w-full max-w-6xl overflow-hidden rounded-3xl border border-white/10 bg-[#0b1220] px-8 py-20 text-center">
          <AnimatedBackground grid={false} priceLine candles />
          <Reveal className="relative">
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
              <Link to="/developers" className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/5">
                View pricing
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
