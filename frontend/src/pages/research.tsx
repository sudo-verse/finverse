import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, History, Microscope, Plus, Send, Sparkles, Square, Swords } from "lucide-react";
import { streamResearchChat, streamResearchCompare, type StreamCallbacks } from "@/api/research";
import { HistoryDrawer } from "@/components/research/history-drawer";
import { ResearchHero, SUGGESTED_QUESTIONS } from "@/components/research/research-hero";
import { ResearchMessageBubble } from "@/components/research/research-message";
import { SourcesPanel } from "@/components/research/sources-panel";
import { TemplateBar } from "@/components/research/template-bar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import type { ResearchCompany, ResearchHistoryItem, ResearchMessage } from "@/types";

function makeUserMessage(content: string): ResearchMessage {
  return { id: `u-${Date.now()}`, role: "user", content, timestamp: new Date().toISOString() };
}

function makeDraftMessage(): ResearchMessage {
  return {
    id: `a-${Date.now()}`,
    role: "assistant",
    content: "",
    timestamp: new Date().toISOString(),
    streaming: true,
  };
}

function stubCompany(symbol: string): ResearchCompany {
  return { symbol, name: symbol, industry: null, indexedChunks: 0 };
}

export default function ResearchPage() {
  // /research/:symbol deep-links (e.g. from the Document Center) open the
  // chat with that company pre-selected.
  const { symbol: urlSymbol } = useParams<{ symbol: string }>();
  const [company, setCompany] = useState<ResearchCompany | null>(() =>
    urlSymbol ? stubCompany(urlSymbol.toUpperCase()) : null,
  );
  const [pair, setPair] = useState<[ResearchCompany, ResearchCompany] | null>(null);
  const [messages, setMessages] = useState<ResearchMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const inChat = company !== null || pair !== null;
  const contextLabel = pair ? `${pair[0].symbol} vs ${pair[1].symbol}` : (company?.symbol ?? "");
  const contextName = pair ? `${pair[0].name} and ${pair[1].name}` : (company?.name ?? "");

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  /** Core sender — explicit base/target args so regenerate and auto-send
   *  don't race against not-yet-committed state. */
  const sendCore = (
    text: string,
    base: ResearchMessage[],
    single: ResearchCompany | null,
    duo: [ResearchCompany, ResearchCompany] | null,
  ) => {
    const trimmed = text.trim();
    if (!trimmed || busy || (!single && !duo)) return;

    const draft = makeDraftMessage();
    const draftId = draft.id;
    const history = base
      .filter((m) => !m.streaming && !m.error && m.content)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));

    setMessages([...base, makeUserMessage(trimmed), draft]);
    setInput("");
    setBusy(true);

    const patch = (p: Partial<ResearchMessage>) =>
      setMessages((prev) => prev.map((m) => (m.id === draftId ? { ...m, ...p } : m)));

    const callbacks: StreamCallbacks = {
      onSources: (sources) => patch({ sources }),
      onDelta: (t) =>
        setMessages((prev) => prev.map((m) => (m.id === draftId ? { ...m, content: m.content + t } : m))),
      onDone: (final) =>
        patch({
          content: final.content,
          sources: final.sources,
          followUps: final.followUps,
          streaming: false,
        }),
      onError: (detail) => {
        patch({ streaming: false, error: true });
        toast.error(detail);
      },
    };

    const controller = new AbortController();
    abortRef.current = controller;
    const request = duo
      ? streamResearchCompare({ symbols: [duo[0].symbol, duo[1].symbol], message: trimmed }, callbacks, controller.signal)
      : streamResearchChat({ symbol: single!.symbol, message: trimmed, history }, callbacks, controller.signal);

    request
      .catch((e: unknown) => {
        if ((e as Error).name === "AbortError") patch({ streaming: false }); // user hit Stop — keep partial text
        else callbacks.onError("Failed to reach the research copilot.");
      })
      .finally(() => setBusy(false));
  };

  const send = (text: string) => sendCore(text, messages, company, pair);

  const regenerate = () => {
    const lastUserIdx = messages.map((m) => m.role).lastIndexOf("user");
    if (lastUserIdx === -1) return;
    sendCore(messages[lastUserIdx].content, messages.slice(0, lastUserIdx), company, pair);
  };

  const stop = () => abortRef.current?.abort();

  const selectCompany = (c: ResearchCompany) => {
    setCompany(c);
    setPair(null);
    setMessages([]);
    if (pendingQuestion) {
      sendCore(pendingQuestion, [], c, null);
      setPendingQuestion(null);
    }
  };

  const startCompare = (a: ResearchCompany, b: ResearchCompany) => {
    setPair([a, b]);
    setCompany(null);
    setMessages([]);
    sendCore(`Compare ${a.name} (${a.symbol}) and ${b.name} (${b.symbol}).`, [], null, [a, b]);
  };

  const reset = () => {
    stop();
    setCompany(null);
    setPair(null);
    setMessages([]);
    setPendingQuestion(null);
  };

  const openHistoryItem = (item: ResearchHistoryItem) => {
    setHistoryOpen(false);
    const symbols = (item.symbol ?? "").split(" vs ");
    if (item.mode === "compare" && symbols.length === 2) {
      setPair([stubCompany(symbols[0]), stubCompany(symbols[1])]);
      setCompany(null);
    } else {
      setCompany(stubCompany(item.symbol ?? ""));
      setPair(null);
    }
    setMessages([
      { ...makeUserMessage(item.question), id: `h-u-${item.id}` },
      {
        id: `h-a-${item.id}`,
        role: "assistant",
        content: item.answer ?? "",
        timestamp: item.createdAt,
        sources: item.sources,
      },
    ]);
  };

  /* ------------------------------- landing ------------------------------- */
  if (!inChat) {
    return (
      <div className="relative">
        <div className="absolute right-0 top-0">
          <Button variant="outline" size="sm" onClick={() => setHistoryOpen(true)}>
            <History className="h-3.5 w-3.5" /> History
          </Button>
        </div>
        <ResearchHero
          pendingQuestion={pendingQuestion}
          onPickSuggestion={setPendingQuestion}
          onSelect={selectCompany}
          onCompare={startCompare}
        />
        <HistoryDrawer open={historyOpen} onOpenChange={setHistoryOpen} onPick={openHistoryItem} />
      </div>
    );
  }

  /* --------------------------------- chat -------------------------------- */
  return (
    <div className="flex h-[calc(100vh-7.5rem)] flex-col">
      {/* Header */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Button variant="ghost" size="icon" onClick={reset} aria-label="Back to company selection">
          <ArrowLeft />
        </Button>
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-600 shadow-lg shadow-emerald-500/20">
            {pair ? <Swords className="h-4.5 w-4.5 text-white" /> : <Microscope className="h-4.5 w-4.5 text-white" />}
          </div>
          <div className="min-w-0 leading-tight">
            <h1 className="flex items-center gap-2 truncate text-lg font-bold tracking-tight">
              {contextLabel}
              <Badge className="normal-case tracking-normal">
                <Sparkles className="h-3 w-3" /> {pair ? "Compare" : "Research"}
              </Badge>
            </h1>
            <p className="truncate text-xs text-muted-foreground">{contextName}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setHistoryOpen(true)}>
            <History className="h-3.5 w-3.5" /> History
          </Button>
          <Button variant="outline" size="sm" onClick={() => setMessages([])} disabled={busy || messages.length === 0}>
            <Plus className="h-3.5 w-3.5" /> New chat
          </Button>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 xl:grid-cols-[1fr_310px]">
        {/* Chat column */}
        <Card className="flex min-h-0 flex-col overflow-hidden">
          <div ref={scrollRef} className="min-h-0 flex-1 space-y-5 overflow-y-auto p-4 md:p-6">
            {messages.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                <p className="max-w-sm text-sm text-muted-foreground">
                  Ask anything about <span className="font-medium text-foreground">{contextName}</span> — filings,
                  results, risks, strategy. Answers cite their sources.
                </p>
                <div className="flex max-w-md flex-wrap justify-center gap-2">
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => send(q)}
                      className="cursor-pointer rounded-full border border-border/70 bg-secondary/40 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <ResearchMessageBubble
                key={m.id}
                message={m}
                symbol={company?.symbol ?? ""}
                isLastAssistant={m.role === "assistant" && i === messages.length - 1}
                busy={busy}
                onRegenerate={regenerate}
                onFollowUp={send}
              />
            ))}
          </div>

          {/* Templates + composer */}
          <div className="border-t border-border/60 p-3 md:p-4">
            <TemplateBar
              companyName={pair ? contextLabel : (company?.name ?? "")}
              disabled={busy}
              onPick={send}
              className="mb-2.5"
            />
            <div className="flex items-end gap-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send(input);
                  }
                }}
                placeholder={`Ask about ${contextLabel}…  (Enter to send)`}
                rows={1}
                className="max-h-32 min-h-[44px] flex-1"
              />
              {busy ? (
                <Button className="shrink-0" size="icon" variant="outline" onClick={stop} aria-label="Stop generating">
                  <Square className="h-3.5 w-3.5" />
                </Button>
              ) : (
                <Button className="shrink-0" size="icon" disabled={!input.trim()} onClick={() => send(input)} aria-label="Send">
                  <Send />
                </Button>
              )}
            </div>
            <p className="mt-2 text-center text-[10px] text-muted-foreground/70">
              Grounded in indexed filings and Finverse data. Automated research — not investment advice.
            </p>
          </div>
        </Card>

        {/* Sources sidebar */}
        <div className="hidden min-h-0 space-y-4 overflow-y-auto xl:block">
          {pair ? (
            <>
              <SourcesPanel symbol={pair[0].symbol} />
              <SourcesPanel symbol={pair[1].symbol} />
            </>
          ) : (
            <SourcesPanel symbol={company!.symbol} />
          )}
        </div>
      </div>

      <HistoryDrawer open={historyOpen} onOpenChange={setHistoryOpen} onPick={openHistoryItem} />
    </div>
  );
}
