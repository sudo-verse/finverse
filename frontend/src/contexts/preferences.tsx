import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

/**
 * User preferences, persisted to localStorage (per-device). These are real and
 * applied immediately — the accent colour overrides the `--primary` CSS token
 * live. Server-side sync is a future enhancement; for now everything here is
 * honestly local to the browser.
 */
export type Accent = "blue" | "emerald" | "violet" | "amber";

/** NSE index universe used to personalise ranked lists. */
export type Universe = "all" | "nifty50" | "nifty100" | "nifty200" | "nifty500";

export const UNIVERSES: { key: Universe; label: string }[] = [
  { key: "all", label: "All stocks" },
  { key: "nifty50", label: "Nifty 50" },
  { key: "nifty100", label: "Nifty 100" },
  { key: "nifty200", label: "Nifty 200" },
  { key: "nifty500", label: "Nifty 500" },
];

export interface NotificationPrefs {
  buy: boolean;
  sell: boolean;
  news: boolean;
  telegram: boolean;
}

export interface Preferences {
  accent: Accent;
  universe: Universe;
  notifications: NotificationPrefs;
}

const DEFAULTS: Preferences = {
  accent: "blue",
  universe: "all",
  notifications: { buy: true, sell: true, news: false, telegram: false },
};

const UNIVERSE_KEYS = UNIVERSES.map((u) => u.key);

/** Accent → (primary, primary-foreground, ring). */
export const ACCENTS: Record<Accent, { label: string; primary: string; foreground: string }> = {
  blue: { label: "Terminal Blue", primary: "#3b82f6", foreground: "#f8fafc" },
  emerald: { label: "Emerald", primary: "#10b981", foreground: "#04150f" },
  violet: { label: "Violet", primary: "#8b5cf6", foreground: "#f8fafc" },
  amber: { label: "Amber", primary: "#f59e0b", foreground: "#1a1203" },
};

const STORAGE_KEY = "finverse:preferences";

function load(): Preferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULTS;
    const parsed = JSON.parse(raw) as Partial<Preferences>;
    return {
      accent: parsed.accent && parsed.accent in ACCENTS ? parsed.accent : DEFAULTS.accent,
      universe: parsed.universe && UNIVERSE_KEYS.includes(parsed.universe) ? parsed.universe : DEFAULTS.universe,
      notifications: { ...DEFAULTS.notifications, ...(parsed.notifications ?? {}) },
    };
  } catch {
    return DEFAULTS;
  }
}

function applyAccent(accent: Accent) {
  const a = ACCENTS[accent] ?? ACCENTS.blue;
  const root = document.documentElement;
  root.style.setProperty("--primary", a.primary);
  root.style.setProperty("--primary-foreground", a.foreground);
  root.style.setProperty("--ring", a.primary);
}

interface PreferencesContextValue {
  prefs: Preferences;
  setAccent: (accent: Accent) => void;
  setUniverse: (universe: Universe) => void;
  setNotification: (key: keyof NotificationPrefs, value: boolean) => void;
  reset: () => void;
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Preferences>(load);

  // Apply + persist on every change (so reload restores, and accent is live).
  useEffect(() => {
    applyAccent(prefs.accent);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch {
      /* storage unavailable (private mode) — preferences stay in-memory */
    }
  }, [prefs]);

  const setAccent = useCallback((accent: Accent) => setPrefs((p) => ({ ...p, accent })), []);
  const setUniverse = useCallback((universe: Universe) => setPrefs((p) => ({ ...p, universe })), []);
  const setNotification = useCallback(
    (key: keyof NotificationPrefs, value: boolean) =>
      setPrefs((p) => ({ ...p, notifications: { ...p.notifications, [key]: value } })),
    [],
  );
  const reset = useCallback(() => setPrefs(DEFAULTS), []);

  const value = useMemo(
    () => ({ prefs, setAccent, setUniverse, setNotification, reset }),
    [prefs, setAccent, setUniverse, setNotification, reset],
  );

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferences(): PreferencesContextValue {
  const ctx = useContext(PreferencesContext);
  if (!ctx) throw new Error("usePreferences must be used within a PreferencesProvider");
  return ctx;
}
