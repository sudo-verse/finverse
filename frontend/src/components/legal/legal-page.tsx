import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, TrendingUp } from "lucide-react";
import { Footer } from "@/components/layout/footer";
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
 * Standalone chrome for the public legal pages (reachable without auth and
 * crawlable). Brand header + back link + section sub-nav + global footer.
 */
export function LegalPage({ title, current, children }: LegalPageProps) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Seo title={title} description={`${title} for Finverse — AI-powered NSE stock intelligence.`} />
      <header className="border-b border-border/60">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-4">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-violet-600 text-white shadow">
              <TrendingUp className="h-4 w-4" />
            </div>
            <span className="text-[15px] font-bold tracking-tight">{LEGAL.company}</span>
          </Link>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" /> Back to app
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">Last updated: {LEGAL.lastUpdated}</p>

        <nav className="mt-6 flex flex-wrap gap-2">
          {LEGAL_LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                l.to === current
                  ? "border-primary/40 bg-primary/15 text-primary"
                  : "border-border/60 text-muted-foreground hover:text-foreground",
              )}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <article className="prose-legal mt-8 space-y-6 text-sm leading-relaxed text-foreground/90">
          {children}
        </article>
      </main>

      <Footer />
    </div>
  );
}

/** Lightweight section helper for consistent legal typography. */
export function Section({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold text-foreground">{heading}</h2>
      <div className="space-y-2 text-muted-foreground">{children}</div>
    </section>
  );
}
