import { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Bell, KeyRound, Palette, Save } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";

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

export default function SettingsPage() {
  const [theme, setTheme] = useState("dark");
  const [accent, setAccent] = useState("blue");
  const [notifBuy, setNotifBuy] = useState(true);
  const [notifSell, setNotifSell] = useState(true);
  const [notifNews, setNotifNews] = useState(false);
  const [notifTelegram, setNotifTelegram] = useState(true);
  const [apiUrl, setApiUrl] = useState("http://localhost:8000/api");
  const [apiKey, setApiKey] = useState("");

  const save = () => toast.success("Settings saved", { description: "Your preferences have been updated." });

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Settings" description="Preferences, alerts and backend configuration" />

      <div className="space-y-5">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-4 w-4 text-primary" /> Appearance
              </CardTitle>
              <CardDescription>Theme preferences for the terminal</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Theme</Label>
                <Select value={theme} onValueChange={setTheme}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dark">Dark (recommended)</SelectItem>
                    <SelectItem value="midnight">Midnight</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Accent colour</Label>
                <Select value={accent} onValueChange={setAccent}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="blue">Terminal Blue</SelectItem>
                    <SelectItem value="emerald">Emerald</SelectItem>
                    <SelectItem value="violet">Violet</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-hold" /> Notifications
              </CardTitle>
              <CardDescription>Choose which events trigger alerts</CardDescription>
            </CardHeader>
            <CardContent className="divide-y divide-border/60">
              <SettingRow label="BUY signal alerts" description="Notify when the engine generates a BUY signal" checked={notifBuy} onChange={setNotifBuy} />
              <SettingRow label="SELL signal alerts" description="Notify when the engine generates a SELL signal" checked={notifSell} onChange={setNotifSell} />
              <SettingRow label="News sentiment alerts" description="Notify on strongly negative news for held stocks" checked={notifNews} onChange={setNotifNews} />
              <SettingRow label="Telegram delivery" description="Forward alerts to the connected Telegram bot" checked={notifTelegram} onChange={setNotifTelegram} />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-chart-4" /> API Configuration
              </CardTitle>
              <CardDescription>Connect the frontend to your Finverse backend</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api-url">Backend URL</Label>
                <Input id="api-url" value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} className="font-mono text-xs" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="api-key">API key</Label>
                <Input
                  id="api-key"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="fv_••••••••••••••••"
                  className="font-mono text-xs"
                />
                <p className="text-xs text-muted-foreground">
                  Stored locally in your browser. The app talks to the live backend via <code className="font-mono">/api</code>.
                </p>
              </div>
              <Separator />
              <div className="flex justify-end">
                <Button onClick={save}>
                  <Save /> Save changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
