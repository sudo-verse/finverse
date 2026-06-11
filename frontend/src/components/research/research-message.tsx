import { useState } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import { toast } from "sonner";
import { AlertTriangle, Check, Copy, RefreshCw, Sparkles, User } from "lucide-react";
import { SourceCitations } from "@/components/research/source-citations";
import { cn } from "@/lib/utils";
import type { ResearchMessage } from "@/types";
import "highlight.js/styles/github-dark.css";

interface ResearchMessageBubbleProps {
  message: ResearchMessage;
  symbol: string;
  isLastAssistant: boolean;
  busy: boolean;
  onRegenerate: () => void;
  onFollowUp: (question: string) => void;
}

export function ResearchMessageBubble({
  message,
  symbol,
  isLastAssistant,
  busy,
  onRegenerate,
  onFollowUp,
}: ResearchMessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Could not copy to clipboard");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn("group flex gap-3", isUser && "flex-row-reverse")}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          isUser
            ? "bg-secondary text-muted-foreground"
            : "bg-gradient-to-br from-emerald-500 to-cyan-600 text-white shadow-lg shadow-emerald-500/20",
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
      </div>

      <div
        className={cn(
          "max-w-[88%] space-y-1 rounded-2xl px-4 py-3 text-sm leading-relaxed md:max-w-[76%]",
          isUser
            ? "rounded-tr-sm bg-primary/15 text-foreground"
            : "rounded-tl-sm bg-secondary/60 text-foreground/90",
          message.error && "border border-bear/40",
        )}
      >
        {message.error && (
          <p className="flex items-center gap-1.5 text-xs font-medium text-bear">
            <AlertTriangle className="h-3.5 w-3.5" /> Generation failed
          </p>
        )}

        <div className="prose-finverse">
          <ReactMarkdown rehypePlugins={[rehypeHighlight]}>{message.content}</ReactMarkdown>
          {message.streaming && (
            <motion.span
              className="ml-0.5 inline-block h-4 w-1.5 translate-y-0.5 rounded-sm bg-primary"
              animate={{ opacity: [1, 0.2, 1] }}
              transition={{ duration: 0.9, repeat: Infinity }}
            />
          )}
        </div>

        {!isUser && !message.streaming && message.sources && (
          <SourceCitations sources={message.sources} symbol={symbol} />
        )}

        {/* Actions */}
        {!isUser && !message.streaming && message.content && (
          <div className="flex items-center gap-1 pt-1.5 opacity-0 transition-opacity group-hover:opacity-100">
            <button
              type="button"
              onClick={copy}
              className="flex cursor-pointer items-center gap-1 rounded-md px-1.5 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              {copied ? <Check className="h-3 w-3 text-bull" /> : <Copy className="h-3 w-3" />}
              {copied ? "Copied" : "Copy"}
            </button>
            {isLastAssistant && (
              <button
                type="button"
                disabled={busy}
                onClick={onRegenerate}
                className="flex cursor-pointer items-center gap-1 rounded-md px-1.5 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-50"
              >
                <RefreshCw className="h-3 w-3" /> Regenerate
              </button>
            )}
          </div>
        )}

        {/* Follow-up suggestions */}
        {!isUser && !message.streaming && isLastAssistant && (message.followUps?.length ?? 0) > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-2">
            {message.followUps!.map((q) => (
              <button
                key={q}
                type="button"
                disabled={busy}
                onClick={() => onFollowUp(q)}
                className="cursor-pointer rounded-full border border-primary/25 bg-primary/8 px-2.5 py-1 text-[11px] text-primary/90 transition-colors hover:bg-primary/15 disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
