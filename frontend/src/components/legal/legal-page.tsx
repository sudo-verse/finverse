import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { Seo } from "@/components/seo";
import { LEGAL, LEGAL_LINKS } from "@/lib/legal";
import { cn } from "@/lib/utils";

interface LegalPageProps {
  title: string;
  /** Active legal route, to highlight in the sub-nav. */
  current: string;
  children: ReactNode;
}

/**
 * Standalone chrome for the public legal pages — light, premium, shared with
 * the rest of the marketing surface.
 */
export function LegalPage({ title, current, children }: LegalPageProps) {
  return (
    <div className="flex min-h-screen flex-col bg-[#060a13] text-white">
      <Seo title={title} description={`${title} for Finverse — AI-powered NSE stock intelligence.`} />
      <SiteHeader />

      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <h1 className="text-4xl font-bold tracking-tight text-white">{title}</h1>
        <p className="mt-2 text-sm text-zinc-500">Last updated: {LEGAL.lastUpdated}</p>

        <nav className="mt-6 flex flex-wrap gap-2">
          {LEGAL_LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                l.to === current
                  ? "border-blue-500/50 bg-blue-500/15 text-blue-300"
                  : "border-white/15 text-zinc-400 hover:text-white",
              )}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <article className="mt-10 space-y-8 text-sm leading-relaxed text-zinc-400">
          {children}
        </article>
      </main>

      <SiteFooter />
    </div>
  );
}

/** Lightweight section helper for consistent legal typography. */
export function Section({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold text-white">{heading}</h2>
      <div className="space-y-2 text-zinc-400">{children}</div>
    </section>
  );
}
