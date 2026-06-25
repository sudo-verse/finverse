import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { reportError } from "@/lib/sentry";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * App-wide error boundary so a render exception shows a friendly fallback
 * instead of a blank white screen. Uses plain anchors (not router links) so it
 * works even if routing is what failed. Wire a real error monitor (Sentry) in
 * componentDidCatch when available.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    reportError(error, { componentStack: info.componentStack });
    console.error("Uncaught render error:", error, info);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
        <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-bear/15 text-bear">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight">Something went wrong</h1>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          An unexpected error occurred while rendering this page. Reloading usually fixes it. If it keeps
          happening, please let us know.
        </p>
        {import.meta.env.DEV && this.state.error && (
          <pre className="mt-4 max-w-lg overflow-auto rounded-lg border border-border/60 bg-card/60 p-3 text-left text-xs text-bear">
            {this.state.error.message}
          </pre>
        )}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={this.handleReload}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Reload page
          </button>
          <a
            href="/"
            className="inline-flex items-center gap-2 rounded-lg border border-border/60 px-4 py-2 text-sm font-medium text-foreground hover:bg-accent/60"
          >
            Go to dashboard
          </a>
        </div>
      </div>
    );
  }
}
