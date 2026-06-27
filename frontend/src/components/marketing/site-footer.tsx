import { useState, type SVGProps } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { LEGAL, SHORT_DISCLAIMER } from "@/lib/legal";
import { BrandMark } from "./site-header";

// Brand glyphs (this lucide build ships no brand icons).
function IconLinkedin(p: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...p}>
      <path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9h4v12H3V9Zm6 0h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V21h-4v-5.5c0-1.3-.03-3-1.83-3-1.83 0-2.11 1.43-2.11 2.9V21H9V9Z" />
    </svg>
  );
}
function IconX(p: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...p}>
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24h-6.656l-5.214-6.817-5.966 6.817H1.683l7.73-8.835L1.254 2.25H8.08l4.713 6.231 5.45-6.231Zm-1.161 17.52h1.833L7.084 4.126H5.117L17.083 19.77Z" />
    </svg>
  );
}
function IconGithub(p: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...p}>
      <path d="M12 2C6.48 2 2 6.58 2 12.25c0 4.53 2.87 8.37 6.84 9.73.5.1.68-.22.68-.49v-1.7c-2.78.62-3.37-1.21-3.37-1.21-.46-1.18-1.11-1.5-1.11-1.5-.9-.63.07-.62.07-.62 1 .07 1.53 1.05 1.53 1.05.89 1.57 2.34 1.12 2.91.85.09-.66.35-1.12.63-1.38-2.22-.26-4.56-1.14-4.56-5.06 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05a9.3 9.3 0 0 1 5 0c1.91-1.32 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.93-2.34 4.79-4.57 5.05.36.32.68.94.68 1.9v2.82c0 .27.18.6.69.49A10.26 10.26 0 0 0 22 12.25C22 6.58 17.52 2 12 2Z" />
    </svg>
  );
}
const SOCIALS = [IconLinkedin, IconX, IconGithub];

const COLUMNS: { heading: string; links: { label: string; to: string }[] }[] = [
  {
    heading: "Product",
    links: [
      { label: "Features", to: "/#features" },
      { label: "Pricing", to: "/pricing" },
      { label: "API & docs", to: "/developers" },
      { label: "Sign in", to: "/login" },
    ],
  },
  {
    heading: "Resources",
    links: [
      { label: "Conviction Score", to: "/login" },
      { label: "Fair Value", to: "/login" },
      { label: "Smart Money", to: "/login" },
      { label: "IPO Tracker", to: "/login" },
    ],
  },
  {
    heading: "Company",
    links: [
      { label: "Terms", to: "/terms" },
      { label: "Privacy", to: "/privacy" },
      { label: "Disclaimer", to: "/disclaimer" },
      { label: "Contact", to: "/developers" },
    ],
  },
];

export function SiteFooter() {
  const year = new Date().getFullYear();
  const [email, setEmail] = useState("");

  const subscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    toast.success("You're on the list — we'll be in touch.");
    setEmail("");
  };

  return (
    <footer className="relative overflow-hidden border-t border-white/10 bg-[#070b15]">
      <div className="mx-auto w-full max-w-6xl px-6 pt-16">
        <div className="grid gap-12 lg:grid-cols-[1.2fr_1fr_1fr_1.4fr]">
          {COLUMNS.map((col) => (
            <div key={col.heading}>
              <h4 className="text-sm font-semibold text-blue-400">{col.heading}</h4>
              <ul className="mt-5 space-y-3">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link to={l.to} className="text-sm text-zinc-400 transition-colors hover:text-white">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {/* Newsletter */}
          <div>
            <h4 className="text-lg font-semibold leading-snug text-white">
              Get the edge in your inbox
            </h4>
            <p className="mt-2 text-sm text-zinc-400">Market intelligence and product updates. No spam.</p>
            <form onSubmit={subscribe} className="mt-4">
              <div className="rounded-lg border border-white/15 bg-white/5 px-4 py-3 transition-colors focus-within:border-blue-500/50">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Your email"
                  className="w-full bg-transparent text-sm text-white placeholder:text-zinc-500 outline-none"
                  aria-label="Email"
                />
              </div>
              <button
                type="submit"
                className="mt-3 w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-500"
              >
                Subscribe
              </button>
            </form>
            <div className="mt-5 flex items-center gap-3">
              {SOCIALS.map((Icon, i) => (
                <a
                  key={i}
                  href="#"
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 text-zinc-400 transition-colors hover:border-white/25 hover:text-white"
                  aria-label="Social link"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Watermark wordmark */}
        <div className="relative mt-12 flex items-center gap-4 overflow-hidden">
          <BrandMark className="h-12 w-12 shrink-0 fv-float" />
          <span
            className="select-none whitespace-nowrap text-[12vw] font-bold leading-none tracking-tighter text-transparent lg:text-[150px]"
            style={{ WebkitTextStroke: "1px rgba(147,197,253,0.16)" }}
            aria-hidden
          >
            Finverse
          </span>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col gap-4 border-t border-white/10 py-7 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            <span className="text-sm text-zinc-400">All systems operational</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-sm text-zinc-500">© {year} {LEGAL.company}</span>
            <Link to="/privacy" className="text-sm text-zinc-400 hover:text-white">Privacy</Link>
            <Link to="/terms" className="text-sm text-zinc-400 hover:text-white">Terms</Link>
          </div>
        </div>
        <p className="pb-8 text-xs leading-relaxed text-zinc-600">{SHORT_DISCLAIMER}</p>
      </div>
    </footer>
  );
}
