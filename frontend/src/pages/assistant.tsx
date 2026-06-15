import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import { Bot, FileText, Paperclip, Send, Sparkles, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useSendChat } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types";

const SUGGESTIONS = [
  "Top 5 stocks by sentiment score",
  "What do the ingested documents say about revenue growth?",
  "Summarise the key risks mentioned in the filings",
  "Which stocks have the weakest sentiment?",
];

function makeUserMessage(content: string): ChatMessage {
  return {
    id: `u-${Date.now()}`,
    role: "user",
    content,
    timestamp: new Date().toISOString(),
  };
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi, I'm **Finverse AI** — your research assistant. I answer questions **grounded in the documents ingested into the knowledge base** (annual reports, filings, transcripts) using RAG over ChromaDB + Gemini.\n\nAsk me anything about the indexed documents to get started.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const sendChat = useSendChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sendChat.isPending]);

  const send = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || sendChat.isPending) return;
    setMessages((prev) => [...prev, makeUserMessage(trimmed)]);
    setInput("");
    sendChat.mutate(
      { message: trimmed },
      {
        onSuccess: (reply) => setMessages((prev) => [...prev, reply]),
        onError: (e) => {
          const detail =
            (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            "Failed to reach the assistant. Please try again.";
          toast.error(detail);
        },
      },
    );
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            AI Research Assistant
            <Badge className="normal-case tracking-normal">
              <Sparkles className="h-3 w-3" /> RAG
            </Badge>
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">Document Q&A over filings, reports and transcripts</p>
        </div>
      </div>

      <Card className="flex min-h-0 flex-1 flex-col overflow-hidden">
        {/* Messages */}
        <div ref={scrollRef} className="min-h-0 flex-1 space-y-5 overflow-y-auto p-4 md:p-6">
          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={cn("flex gap-3", m.role === "user" && "flex-row-reverse")}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                    m.role === "assistant"
                      ? "bg-gradient-to-br from-blue-500 to-violet-600 text-white"
                      : "bg-secondary text-muted-foreground",
                  )}
                >
                  {m.role === "assistant" ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
                </div>
                <div
                  className={cn(
                    "max-w-[82%] space-y-1 rounded-2xl px-4 py-3 text-sm leading-relaxed md:max-w-[68%]",
                    m.role === "assistant"
                      ? "rounded-tl-sm bg-secondary/60 text-foreground/90"
                      : "rounded-tr-sm bg-primary/15 text-foreground",
                  )}
                >
                  <div className="prose-finverse">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                  {m.sources && m.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      {m.sources.map((s, i) => (
                        <span
                          key={`${s.source}-${i}`}
                          title={s.snippet}
                          className="flex cursor-help items-center gap-1 rounded-md bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                        >
                          <FileText className="h-2.5 w-2.5" />
                          {s.source}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing indicator */}
          {sendChat.isPending && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 text-white">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-secondary/60 px-4 py-3.5">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-muted-foreground"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </div>

        {/* Suggestions */}
        {messages.length <= 1 && (
          <div className="flex flex-wrap gap-2 px-4 pb-3 md:px-6">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="cursor-pointer rounded-full border border-border/70 bg-secondary/40 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Composer */}
        <div className="border-t border-border/60 p-3 md:p-4">
          <div className="flex items-end gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0"
              aria-label="Attach document"
              onClick={() =>
                toast.info("Ingest documents via the backend: rag.ingest_file() — UI upload coming soon.")
              }
            >
              <Paperclip />
            </Button>
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
              placeholder="Ask about the ingested documents…  (Enter to send)"
              rows={1}
              className="max-h-32 min-h-[44px] flex-1"
            />
            <Button
              className="shrink-0"
              size="icon"
              disabled={!input.trim() || sendChat.isPending}
              onClick={() => send(input)}
              aria-label="Send"
            >
              <Send />
            </Button>
          </div>
          <p className="mt-2 text-center text-[10px] text-muted-foreground/70">
            Answers are grounded in the indexed documents only. Verify important information against original filings.
          </p>
        </div>
      </Card>
    </div>
  );
}
