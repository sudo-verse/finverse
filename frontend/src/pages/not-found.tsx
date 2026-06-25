import { Link } from "react-router-dom";
import { Compass, Home, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
      <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 text-white shadow-md">
        <TrendingUp className="h-6 w-6" />
      </div>
      <p className="font-mono text-6xl font-bold tracking-tight text-primary/80">404</p>
      <h1 className="mt-3 text-2xl font-bold tracking-tight">Page not found</h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        The page you're looking for doesn't exist or may have moved. Check the URL, or head back to your
        dashboard.
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Button asChild>
          <Link to="/">
            <Home className="h-4 w-4" /> Go to dashboard
          </Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/screener">
            <Compass className="h-4 w-4" /> Explore stocks
          </Link>
        </Button>
      </div>
    </div>
  );
}
