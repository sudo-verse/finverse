import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Check, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { LEGAL_LINKS } from "@/lib/legal";
import { useAuth } from "@/contexts/auth";
import { AnimatedBackground } from "@/components/marketing/animated-background";
import { Seo } from "@/components/seo";

const INPUT =
  "w-full rounded-lg border border-white/10 bg-white/5 px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-500 outline-none transition-colors focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/15";

const POINTS = [
  "One explainable conviction score per stock",
  "Smart-money, insider, valuation & technicals",
  "Free tier — and a developer API",
];

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
      navigate(from, { replace: true });
    } catch (err) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        (mode === "login" ? "Login failed." : "Registration failed.");
      toast.error(detail);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen bg-[#060a13] text-white lg:grid-cols-2">
      <Seo title="Sign in" description="Sign in to Finverse — AI-powered NSE stock intelligence." />

      {/* Brand panel */}
      <div className="relative isolate hidden flex-col justify-between overflow-hidden border-r border-white/10 bg-[#0b1220] p-12 lg:flex">
        <AnimatedBackground priceLine candles={false} />
        <Link to="/" className="relative flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
            <TrendingUp className="h-[18px] w-[18px]" />
          </span>
          <span className="text-[15px] font-semibold tracking-tight text-white">Finverse</span>
        </Link>

        <div className="relative max-w-md">
          <h2 className="text-3xl font-bold leading-tight tracking-tight text-white">
            Six market signals.<br />
            <span className="text-blue-300">One conviction score.</span>
          </h2>
          <ul className="mt-8 space-y-4">
            {POINTS.map((p) => (
              <li key={p} className="flex items-start gap-3 text-zinc-300">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/15 ring-1 ring-blue-500/30">
                  <Check className="h-3 w-3 text-blue-300" />
                </span>
                <span className="text-sm leading-relaxed">{p}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs leading-relaxed text-zinc-500">
          Informational & educational only — not investment advice. Source: NSE.
        </p>
      </div>

      {/* Form */}
      <div className="flex flex-col px-6 py-8 sm:px-12">
        <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Back to home
        </Link>

        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-10">
          <div className="lg:hidden">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white">
              <TrendingUp className="h-5 w-5" />
            </span>
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-white lg:mt-0">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h1>
          <p className="mt-1.5 text-sm text-zinc-400">
            {mode === "login" ? "Sign in to your Finverse account." : "Start with the free tier — no card required."}
          </p>

          <form onSubmit={submit} className="mt-8 space-y-4">
            {mode === "register" && (
              <div className="space-y-1.5">
                <label htmlFor="fullName" className="text-sm font-medium text-zinc-300">Name</label>
                <input id="fullName" className={INPUT} value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Jane Investor" autoComplete="name" />
              </div>
            )}
            <div className="space-y-1.5">
              <label htmlFor="email" className="text-sm font-medium text-zinc-300">Email</label>
              <input id="email" type="email" required className={INPUT} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="password" className="text-sm font-medium text-zinc-300">Password</label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                className={INPUT}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === "register" ? "At least 8 characters" : "••••••••"}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
            </div>
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-200 disabled:opacity-60"
            >
              {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-zinc-400">
            {mode === "login" ? "New to Finverse?" : "Already have an account?"}{" "}
            <button
              type="button"
              className="cursor-pointer font-semibold text-white hover:underline"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
            >
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </p>

          <p className="mt-8 text-center text-[11px] leading-relaxed text-zinc-500">
            By continuing you agree to our{" "}
            {LEGAL_LINKS.map((l, i) => (
              <span key={l.to}>
                <Link to={l.to} className="underline hover:text-zinc-300">{l.label}</Link>
                {i < LEGAL_LINKS.length - 1 ? ", " : "."}
              </span>
            ))}
          </p>
        </div>
      </div>
    </div>
  );
}
