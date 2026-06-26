import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { RequireAuth } from "@/components/auth/require-auth";
import { Skeleton } from "@/components/ui/skeleton";

// Route-level code splitting keeps the initial bundle lean.
const LoginPage = lazy(() => import("@/pages/login"));
const DashboardPage = lazy(() => import("@/pages/dashboard"));
const SignalsPage = lazy(() => import("@/pages/signals"));
const StockAnalysisPage = lazy(() => import("@/pages/stock-analysis"));
const CompetitorsPage = lazy(() => import("@/pages/competitors"));
const PortfolioPage = lazy(() => import("@/pages/portfolio"));
const ResearchPage = lazy(() => import("@/pages/research"));
const DocumentsPage = lazy(() => import("@/pages/documents"));
const SentimentPage = lazy(() => import("@/pages/sentiment"));
const WatchlistPage = lazy(() => import("@/pages/watchlist"));
const ScreenerPage = lazy(() => import("@/pages/screener"));
const OwnershipPage = lazy(() => import("@/pages/ownership"));
const DealsPage = lazy(() => import("@/pages/deals"));
const EventsPage = lazy(() => import("@/pages/events"));
const RadarPage = lazy(() => import("@/pages/radar"));
const EarningsPage = lazy(() => import("@/pages/earnings"));
const AnnouncementsPage = lazy(() => import("@/pages/announcements"));
const InsiderPage = lazy(() => import("@/pages/insider"));
const ValuationPage = lazy(() => import("@/pages/valuation"));
const ConvictionPage = lazy(() => import("@/pages/conviction"));
const TechnicalsPage = lazy(() => import("@/pages/technicals"));
const IposPage = lazy(() => import("@/pages/ipos"));
const ResultsCalendarPage = lazy(() => import("@/pages/results-calendar"));
const SuperstarsPage = lazy(() => import("@/pages/superstars"));
const SettingsPage = lazy(() => import("@/pages/settings"));
const TermsPage = lazy(() => import("@/pages/legal/terms"));
const PrivacyPage = lazy(() => import("@/pages/legal/privacy"));
const DisclaimerPage = lazy(() => import("@/pages/legal/disclaimer"));
const NotFoundPage = lazy(() => import("@/pages/not-found"));

function PageFallback() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-56" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-72 w-full rounded-xl" />
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <Suspense fallback={<PageFallback />}>
            <LoginPage />
          </Suspense>
        }
      />
      {/* Public legal pages — reachable without auth and crawlable. */}
      {(
        [
          ["/terms", TermsPage],
          ["/privacy", PrivacyPage],
          ["/disclaimer", DisclaimerPage],
        ] as const
      ).map(([path, Page]) => (
        <Route
          key={path}
          path={path}
          element={
            <Suspense fallback={<PageFallback />}>
              <Page />
            </Suspense>
          }
        />
      ))}
      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route
          index
          element={
            <Suspense fallback={<PageFallback />}>
              <DashboardPage />
            </Suspense>
          }
        />
        {(
          [
            ["/signals", SignalsPage],
            ["/stocks", StockAnalysisPage],
            ["/stocks/:symbol", StockAnalysisPage],
            ["/competitors", CompetitorsPage],
            ["/competitors/:symbol", CompetitorsPage],
            ["/portfolio", PortfolioPage],
            ["/research", ResearchPage],
            ["/research/:symbol", ResearchPage],
            ["/documents", DocumentsPage],
            ["/documents/:symbol", DocumentsPage],
            ["/sentiment", SentimentPage],
            ["/sentiment/:symbol", SentimentPage],
            ["/watchlist", WatchlistPage],
            ["/screener", ScreenerPage],
            ["/ownership", OwnershipPage],
            ["/deals", DealsPage],
            ["/events", EventsPage],
            ["/radar", RadarPage],
            ["/earnings", EarningsPage],
            ["/announcements", AnnouncementsPage],
            ["/insider", InsiderPage],
            ["/valuation", ValuationPage],
            ["/conviction", ConvictionPage],
            ["/technicals", TechnicalsPage],
            ["/ipos", IposPage],
            ["/results", ResultsCalendarPage],
            ["/superstars", SuperstarsPage],
            ["/settings", SettingsPage],
          ] as const
        ).map(([path, Page]) => (
          <Route
            key={path}
            path={path}
            element={
              <Suspense fallback={<PageFallback />}>
                <Page />
              </Suspense>
            }
          />
        ))}
        <Route
          path="*"
          element={
            <Suspense fallback={<PageFallback />}>
              <NotFoundPage />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  );
}
