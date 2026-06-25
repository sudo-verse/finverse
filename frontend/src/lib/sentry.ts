/**
 * Sentry error monitoring, loaded lazily so the SDK ships only when actually
 * configured. No-op without VITE_SENTRY_DSN — local/dev and un-configured
 * deploys pay zero bundle or runtime cost. Set VITE_SENTRY_DSN in the Vercel
 * project env to enable in production.
 */
type SentryModule = typeof import("@sentry/react");

let sentry: SentryModule | null = null;

export async function initSentry(): Promise<void> {
  const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;
  if (!dsn) return;

  const Sentry = await import("@sentry/react");
  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    integrations: [Sentry.browserTracingIntegration()],
    // Conservative sampling — raise once you've sized your Sentry quota.
    tracesSampleRate: 0.1,
    sendDefaultPii: false,
  });
  sentry = Sentry;
}

/** Report a caught error (no-op until/unless Sentry is initialised). */
export function reportError(error: unknown, context?: Record<string, unknown>): void {
  sentry?.captureException(error, context ? { extra: context } : undefined);
}
