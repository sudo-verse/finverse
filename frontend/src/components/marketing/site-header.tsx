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

/** Brand mark — a solid blue tile with the trend glyph (no gradient). */
export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white",
        className,
      )}
    >
      <TrendingUp className="h-[18px] w-[18px]" />
    </span>
  );
}

/** Sticky dark navigation for the public marketing surface. */
export function SiteHeader() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#070b15]/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2.5">
          <BrandMark />
          <span className="text-[15px] font-semibold tracking-tight text-white">Finverse</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV.map((n) => (
            <a key={n.label} href={n.href} className="text-sm font-medium text-zinc-400 transition-colors hover:text-white">
              {n.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {user ? (
            <Link to="/dashboard" className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-200">
              Open app
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-zinc-400 transition-colors hover:text-white">
                Sign in
              </Link>
              <Link to="/login" className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-200">
                Get started
              </Link>
            </>
          )}
        </div>

        <button type="button" className="text-zinc-300 md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Toggle menu">
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-white/10 bg-[#070b15] px-6 py-4 md:hidden">
          <nav className="flex flex-col gap-3">
            {NAV.map((n) => (
              <a key={n.label} href={n.href} onClick={() => setOpen(false)} className="text-sm font-medium text-zinc-300">
                {n.label}
              </a>
            ))}
            <Link to={user ? "/dashboard" : "/login"} className="mt-2 rounded-lg bg-white px-4 py-2 text-center text-sm font-semibold text-zinc-900">
              {user ? "Open app" : "Get started"}
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
