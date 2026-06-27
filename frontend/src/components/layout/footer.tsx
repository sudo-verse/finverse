import { Link } from "react-router-dom";
import { LEGAL, LEGAL_LINKS, SHORT_DISCLAIMER } from "@/lib/legal";

/**
 * Global footer — legal links, support contact, copyright and the persistent
 * "not investment advice" disclaimer required on a financial product.
 */
export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="mt-10 border-t border-border/60 px-4 py-6 text-xs text-muted-foreground md:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span className="font-medium text-foreground/70">
            © {year} {LEGAL.company} · NSE market intelligence
          </span>
          <nav className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <Link to="/developers" className="hover:text-foreground hover:underline">
              API
            </Link>
            <Link to="/pricing" className="hover:text-foreground hover:underline">
              Pricing
            </Link>
            {LEGAL_LINKS.map((l) => (
              <Link key={l.to} to={l.to} className="hover:text-foreground hover:underline">
                {l.label}
              </Link>
            ))}
            <a href={`mailto:${LEGAL.supportEmail}`} className="hover:text-foreground hover:underline">
              Contact
            </a>
          </nav>
        </div>
        <p className="max-w-4xl leading-relaxed text-muted-foreground/80">{SHORT_DISCLAIMER}</p>
      </div>
    </footer>
  );
}
