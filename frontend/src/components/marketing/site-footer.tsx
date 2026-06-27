import { Link } from "react-router-dom";
import { LEGAL, SHORT_DISCLAIMER } from "@/lib/legal";
import { BrandMark } from "./site-header";

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
    heading: "Legal",
    links: [
      { label: "Terms", to: "/terms" },
      { label: "Privacy", to: "/privacy" },
      { label: "Disclaimer", to: "/disclaimer" },
    ],
  },
];

/** Light footer for the public marketing surface. */
export function SiteFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-zinc-200 bg-white">
      <div className="mx-auto w-full max-w-6xl px-6 py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr]">
          <div>
            <Link to="/" className="flex items-center gap-2.5">
              <BrandMark />
              <span className="text-[15px] font-semibold tracking-tight text-zinc-900">Finverse</span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-zinc-500">
              AI-powered intelligence for the Indian markets — conviction scores, fair value, smart-money
              flows and more, over a clean API.
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.heading}>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">{col.heading}</h4>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link to={l.to} className="text-sm text-zinc-600 transition-colors hover:text-zinc-900">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 border-t border-zinc-200 pt-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-sm text-zinc-500">© {year} {LEGAL.company} · NSE market intelligence</span>
            <a href={`mailto:${LEGAL.supportEmail}`} className="text-sm text-zinc-500 hover:text-zinc-900">
              {LEGAL.supportEmail}
            </a>
          </div>
          <p className="mt-4 max-w-4xl text-xs leading-relaxed text-zinc-400">{SHORT_DISCLAIMER}</p>
        </div>
      </div>
    </footer>
  );
}
