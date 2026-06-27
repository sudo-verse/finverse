import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, TrendingUp, X } from "lucide-react";
import { useAuth } from "@/contexts/auth";
import { cn } from "@/lib/utils";

const NAV = [
  { label: "Features", href: "/#features" },
  { label: "Pricing", href: "/pricing" },
  { label: "API", href: "/developers" },
];

/** Brand mark — a solid black tile, deliberately understated (no gradient). */
export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-white",
        className,
      )}
    >
      <TrendingUp className="h-[18px] w-[18px]" />
    </span>
  );
}

/**
 * Sticky top navigation for the public marketing surface. Light, restrained,
 * generous — the langchain-class chrome that frames every public page.
 */
export function SiteHeader() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-200/70 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2.5">
          <BrandMark />
          <span className="text-[15px] font-semibold tracking-tight text-zinc-900">Finverse</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV.map((n) => (
            <a key={n.label} href={n.href} className="text-sm font-medium text-zinc-600 transition-colors hover:text-zinc-900">
              {n.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {user ? (
            <Link
              to="/dashboard"
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
            >
              Open app
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-zinc-600 transition-colors hover:text-zinc-900">
                Sign in
              </Link>
              <Link
                to="/login"
                className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
              >
                Get started
              </Link>
            </>
          )}
        </div>

        <button
          type="button"
          className="text-zinc-700 md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-zinc-200 bg-white px-6 py-4 md:hidden">
          <nav className="flex flex-col gap-3">
            {NAV.map((n) => (
              <a key={n.label} href={n.href} onClick={() => setOpen(false)} className="text-sm font-medium text-zinc-700">
                {n.label}
              </a>
            ))}
            <Link to={user ? "/dashboard" : "/login"} className="mt-2 rounded-lg bg-zinc-900 px-4 py-2 text-center text-sm font-medium text-white">
              {user ? "Open app" : "Get started"}
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
