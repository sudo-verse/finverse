import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Copy, KeyRound, Loader2, Plus, Trash2, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useApiKeys, useCreateApiKey, useDeleteApiKey } from "@/hooks/queries";
import type { ApiKeyCreated, ApiScope } from "@/types";
import { cn } from "@/lib/utils";

const SCOPES: { value: ApiScope; label: string; hint: string }[] = [
  { value: "read", label: "Read", hint: "GET market & stock data" },
  { value: "ai", label: "AI", hint: "AI research & reports" },
  { value: "write", label: "Write", hint: "Mutate account data" },
];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={() => {
        navigator.clipboard?.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
    >
      {copied ? <Check className="h-3.5 w-3.5 text-bull" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied" : "Copy"}
    </Button>
  );
}

function fmtDate(s: string | null): string {
  if (!s) return "never";
  return new Date(s).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

/**
 * Developer API key management — create, view (masked) and revoke keys for the
 * public Finverse API. The raw secret is shown exactly once, right after
 * creation, in a one-time banner.
 */
export function ApiKeysCard({ autoProvision = false }: { autoProvision?: boolean }) {
  const { data: keys, isLoading } = useApiKeys();
  const create = useCreateApiKey();
  const remove = useDeleteApiKey();
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<ApiScope[]>(["read", "ai", "write"]);
  const [justCreated, setJustCreated] = useState<ApiKeyCreated | null>(null);
  const provisioned = useRef(false);

  const toggleScope = (s: ApiScope) =>
    setScopes((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));

  const handleCreate = (opts?: { name?: string; scopes?: ApiScope[] }) => {
    const useScopes = opts?.scopes ?? scopes;
    if (useScopes.length === 0) return;
    create.mutate(
      { name: (opts?.name ?? name).trim() || "API key", scopes: useScopes },
      {
        onSuccess: (key) => {
          setJustCreated(key);
          setName("");
        },
      },
    );
  };

  // After a successful checkout, provision a first key automatically and reveal
  // its secret once — so paying immediately yields a usable key. Skipped if the
  // user already has keys (avoids surprise extra keys).
  useEffect(() => {
    if (!autoProvision || provisioned.current || isLoading) return;
    if (keys && keys.length === 0 && !create.isPending) {
      provisioned.current = true;
      handleCreate({ name: "default", scopes: ["read", "ai", "write"] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoProvision, isLoading, keys]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-primary" /> Developer API keys
        </CardTitle>
        <CardDescription>
          Authenticate to the public API with a bearer key. See the{" "}
          <Link to="/developers" className="text-primary hover:underline">API docs &amp; pricing</Link>.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* One-time secret reveal */}
        {justCreated && (
          <div className="space-y-2 rounded-lg border border-primary/40 bg-primary/[0.06] p-3">
            <p className="flex items-center gap-1.5 text-sm font-medium text-primary">
              <TriangleAlert className="h-4 w-4" /> Copy your key now — it won't be shown again.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 overflow-x-auto rounded bg-background/60 px-2 py-1.5 font-mono text-xs">
                {justCreated.key}
              </code>
              <CopyButton text={justCreated.key} />
            </div>
            <Button variant="ghost" size="sm" onClick={() => setJustCreated(null)}>
              Done
            </Button>
          </div>
        )}

        {/* Create */}
        <div className="space-y-2">
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              placeholder="Key name (e.g. production)"
              value={name}
              maxLength={64}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
            <Button onClick={() => handleCreate()} disabled={create.isPending || scopes.length === 0}>
              {create.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Create key
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-muted-foreground">Scopes:</span>
            {SCOPES.map((s) => {
              const on = scopes.includes(s.value);
              return (
                <button
                  key={s.value}
                  type="button"
                  title={s.hint}
                  onClick={() => toggleScope(s.value)}
                  aria-pressed={on}
                  className={cn(
                    "rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                    on
                      ? "border-primary/40 bg-primary/15 text-primary"
                      : "border-border/60 text-muted-foreground hover:text-foreground",
                  )}
                >
                  {s.label}
                </button>
              );
            })}
            {scopes.length === 0 && <span className="text-xs text-bear">Pick at least one scope.</span>}
          </div>
        </div>
        {create.isError && (
          <p className="text-xs text-bear">
            {(create.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
              "Could not create key."}
          </p>
        )}

        {/* List */}
        <div className="divide-y divide-border/60">
          {isLoading ? (
            <p className="py-3 text-sm text-muted-foreground">Loading…</p>
          ) : !keys || keys.length === 0 ? (
            <p className="py-3 text-sm text-muted-foreground">No API keys yet.</p>
          ) : (
            keys.map((k) => (
              <div key={k.id} className="flex items-center justify-between gap-4 py-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="truncate text-sm font-medium">{k.name}</p>
                    {k.scopes.map((s) => (
                      <span
                        key={s}
                        className="rounded-full border border-border/60 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                  <p className="font-mono text-xs text-muted-foreground">
                    {k.prefix}…{k.last4}
                  </p>
                  <p className="text-[11px] text-muted-foreground/80">
                    Created {fmtDate(k.createdAt)} · last used {fmtDate(k.lastUsedAt)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-bear hover:text-bear"
                  disabled={remove.isPending}
                  onClick={() => {
                    if (confirm(`Revoke "${k.name}"? Apps using it will stop working immediately.`)) {
                      remove.mutate(k.id);
                    }
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5" /> Revoke
                </Button>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
