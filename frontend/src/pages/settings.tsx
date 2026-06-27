import { motion } from "framer-motion";
import { Bell, Check, LogOut, Palette, UserCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Seo } from "@/components/seo";
import { ApiKeysCard } from "@/components/settings/api-keys";
import { useAuth } from "@/contexts/auth";
import { ACCENTS, usePreferences, type Accent, type NotificationPrefs } from "@/contexts/preferences";
import { cn } from "@/lib/utils";

function SettingRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}

const NOTIFICATIONS: { key: keyof NotificationPrefs; label: string; description: string }[] = [
  { key: "buy", label: "BUY signal alerts", description: "Notify when the engine generates a BUY signal" },
  { key: "sell", label: "SELL signal alerts", description: "Notify when the engine generates a SELL signal" },
  { key: "news", label: "News sentiment alerts", description: "Notify on strongly negative news for held stocks" },
  { key: "telegram", label: "Telegram delivery", description: "Forward alerts to the connected Telegram bot" },
];

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { prefs, setAccent, setNotification } = usePreferences();

  return (
    <div className="mx-auto max-w-3xl">
      <Seo title="Settings" noIndex />
      <PageHeader title="Settings" description="Preferences and account. Changes save automatically to this browser." />

      <div className="space-y-5">
        {/* Appearance */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-4 w-4 text-primary" /> Appearance
              </CardTitle>
              <CardDescription>
                Accent colour for the terminal. Finverse uses a dark theme; light mode is on the roadmap.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Label>Accent colour</Label>
              <div className="flex flex-wrap gap-3">
                {(Object.keys(ACCENTS) as Accent[]).map((key) => {
                  const a = ACCENTS[key];
                  const active = prefs.accent === key;
                  return (
                    <button
                      key={key}
                      onClick={() => setAccent(key)}
                      className={cn(
                        "flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors",
                        active ? "border-foreground/30 bg-accent/40" : "border-border/60 hover:bg-accent/30",
                      )}
                      aria-pressed={active}
                    >
                      <span
                        className="flex h-5 w-5 items-center justify-center rounded-full"
                        style={{ backgroundColor: a.primary }}
                      >
                        {active && <Check className="h-3 w-3 text-white" />}
                      </span>
                      {a.label}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Notifications */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-hold" /> Notifications
              </CardTitle>
              <CardDescription>Choose which events you want alerts for. Saved to this browser.</CardDescription>
            </CardHeader>
            <CardContent className="divide-y divide-border/60">
              {NOTIFICATIONS.map((n) => (
                <SettingRow
                  key={n.key}
                  label={n.label}
                  description={n.description}
                  checked={prefs.notifications[n.key]}
                  onChange={(v) => setNotification(n.key, v)}
                />
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* Developer API keys */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <ApiKeysCard />
        </motion.div>

        {/* Account */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserCircle className="h-4 w-4 text-chart-4" /> Account
              </CardTitle>
              <CardDescription>Your Finverse account</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-1">
                {user?.fullName && <span className="text-sm font-medium">{user.fullName}</span>}
                <span className="font-mono text-sm text-muted-foreground">{user?.email ?? "—"}</span>
              </div>
              <div className="flex justify-end">
                <Button variant="outline" onClick={logout}>
                  <LogOut className="h-4 w-4" /> Sign out
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
