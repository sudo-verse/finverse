/** AI Research Copilot API — REST reads via axios, chat via fetch-based SSE
 *  streaming (axios cannot consume ReadableStream in the browser). */

import { apiClient } from "./client";
import { UNAUTHORIZED_EVENT, clearToken, getToken } from "@/lib/auth-token";
import type {
  CompanySources,
  ResearchCompany,
  ResearchHistoryItem,
  ResearchMessage,
  SourceCitation,
} from "@/types";

export async function getResearchCompanies(search?: string): Promise<ResearchCompany[]> {
  return (await apiClient.get<ResearchCompany[]>("/research/companies", { params: { search, limit: 500 } })).data;
}

export async function getResearchSources(symbol: string): Promise<CompanySources> {
  return (await apiClient.get<CompanySources>(`/research/sources/${symbol}`)).data;
}

export async function getResearchHistory(symbol?: string, limit = 30): Promise<ResearchHistoryItem[]> {
  return (await apiClient.get<ResearchHistoryItem[]>("/research/history", { params: { symbol, limit } })).data;
}

/* ------------------------------- streaming ------------------------------- */

export interface StreamCallbacks {
  onSources: (sources: SourceCitation[]) => void;
  onDelta: (text: string) => void;
  onDone: (message: ResearchMessage) => void;
  onError: (detail: string) => void;
}

export interface ChatBody {
  symbol: string;
  message: string;
  history: { role: string; content: string }[];
}

export interface CompareBody {
  symbols: string[];
  message?: string;
}

async function streamSSE(path: string, body: object, cb: StreamCallbacks, signal?: AbortSignal) {
  const token = getToken();
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ ...body, stream: true }),
    signal,
  });
  if (res.status === 401) {
    clearToken();
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
  if (!res.ok || !res.body) {
    let detail = `Request failed (${res.status})`;
    try {
      detail = ((await res.json()) as { detail?: string }).detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    cb.onError(detail);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let sawDone = false;

  const dispatch = (frame: string) => {
    let event = "message";
    const dataLines: string[] = [];
    for (const line of frame.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    if (dataLines.length === 0) return;
    const data: unknown = JSON.parse(dataLines.join("\n"));
    if (event === "sources") cb.onSources(data as SourceCitation[]);
    else if (event === "delta") cb.onDelta((data as { text: string }).text);
    else if (event === "done") {
      sawDone = true;
      cb.onDone(data as ResearchMessage);
    } else if (event === "error") {
      sawDone = true; // terminal frame — don't also report "ended unexpectedly"
      cb.onError((data as { detail: string }).detail);
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      if (frame.trim()) dispatch(frame);
    }
  }
  if (!sawDone) cb.onError("The stream ended unexpectedly. Please retry.");
}

export function streamResearchChat(body: ChatBody, cb: StreamCallbacks, signal?: AbortSignal) {
  return streamSSE("/research/chat", body, cb, signal);
}

export function streamResearchCompare(body: CompareBody, cb: StreamCallbacks, signal?: AbortSignal) {
  return streamSSE("/research/compare", body, cb, signal);
}
