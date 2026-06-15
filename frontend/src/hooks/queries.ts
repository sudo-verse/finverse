import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as authApi from "@/api/auth";
import * as research from "@/api/research";
import * as services from "@/api/services";
import {
  addHolding,
  clearHoldings,
  generateReport,
  getCompetitors,
  getDashboard,
  getPortfolio,
  getSignalFacets,
  getSignals,
  getStock,
  getStocks,
  sendChatMessage,
} from "@/api/services";
import type { HoldingCreate, SignalFilters } from "@/types";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
    staleTime: 60_000,
    refetchInterval: 60_000, // embedded news engine sweeps every ~60s
  });
}

export function useSignals(filters: SignalFilters) {
  return useQuery({
    queryKey: ["signals", filters],
    queryFn: () => getSignals(filters),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
    refetchInterval: 60_000, // pick up fresh signals from the live engine
  });
}

export function useSignalFacets() {
  return useQuery({ queryKey: ["signal-facets"], queryFn: getSignalFacets, staleTime: 5 * 60_000 });
}

export function useStocks() {
  return useQuery({ queryKey: ["stocks"], queryFn: () => getStocks(), staleTime: 5 * 60_000 });
}

export function useStock(symbol: string | undefined) {
  return useQuery({
    queryKey: ["stock", symbol],
    queryFn: () => getStock(symbol!),
    enabled: Boolean(symbol),
    staleTime: 60_000,
    retry: false, // 404 = no price data; retrying won't help
  });
}

export function useCompetitors(symbol: string | undefined) {
  return useQuery({
    queryKey: ["competitors", symbol],
    queryFn: () => getCompetitors(symbol!),
    enabled: Boolean(symbol),
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: getPortfolio,
    staleTime: 60_000,
    retry: false, // 404 = empty portfolio, not a transient failure
  });
}

export function useAddHolding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: HoldingCreate) => addHolding(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useClearHoldings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clearHoldings,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/* ------------------------------ Live NSE data ------------------------------ */

export function useLiveQuote(symbol: string | undefined) {
  return useQuery({
    queryKey: ["live-quote", symbol],
    queryFn: () => services.getLiveQuote(symbol!),
    enabled: Boolean(symbol),
    staleTime: 30_000,
    refetchInterval: 30_000, // keep the quote ticking
    retry: false,
  });
}

/** Lazy corporate-data hook: only fires when its tab is active. */
export function useCorporateData<T>(
  kind: string,
  symbol: string | undefined,
  fetcher: (symbol: string) => Promise<T>,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["nse", kind, symbol],
    queryFn: () => fetcher(symbol!),
    enabled: Boolean(symbol) && enabled,
    staleTime: 10 * 60_000,
    retry: false,
  });
}

export function useLivePeers(symbol: string | undefined, quarter = "") {
  return useQuery({
    queryKey: ["live-peers", symbol, quarter],
    queryFn: () => services.getLivePeers(symbol!, quarter),
    enabled: Boolean(symbol),
    staleTime: 60_000,
    retry: false,
  });
}

export function usePeerQuarters(symbol: string | undefined) {
  return useQuery({
    queryKey: ["peer-quarters", symbol],
    queryFn: () => services.getPeerQuarters(symbol!),
    enabled: Boolean(symbol),
    staleTime: 30 * 60_000,
    retry: false,
  });
}

export function useMarketOverview() {
  return useQuery({
    queryKey: ["market-overview"],
    queryFn: services.getMarketOverview,
    staleTime: 30_000,
    refetchInterval: 30_000,
    retry: false,
  });
}

export function useMarketMovers() {
  return useQuery({
    queryKey: ["market-movers"],
    queryFn: services.getMarketMovers,
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useAllIndices() {
  return useQuery({
    queryKey: ["all-indices"],
    queryFn: services.getAllIndices,
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useIndexChart(index: string) {
  return useQuery({
    queryKey: ["index-chart", index],
    queryFn: () => services.getIndexChart(index),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useMarquee() {
  return useQuery({
    queryKey: ["marquee"],
    queryFn: services.getMarquee,
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useTurnover() {
  return useQuery({
    queryKey: ["turnover"],
    queryFn: services.getTurnover,
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function useIntraday(symbol: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["intraday", symbol],
    queryFn: () => services.getIntraday(symbol!),
    enabled: Boolean(symbol) && enabled,
    staleTime: 60_000,
    refetchInterval: enabled ? 60_000 : false,
    retry: false,
  });
}

export function useGenerateReport() {
  return useMutation({
    mutationFn: ({ symbol, useCache }: { symbol: string; useCache?: boolean }) =>
      generateReport(symbol, useCache),
  });
}

export function useSendChat() {
  return useMutation({
    mutationFn: ({ message, symbol }: { message: string; symbol?: string }) =>
      sendChatMessage(message, symbol),
  });
}

/* --------------------------- AI Research Copilot --------------------------- */

export function useResearchCompanies(search?: string) {
  return useQuery({
    queryKey: ["research-companies", search ?? ""],
    queryFn: () => research.getResearchCompanies(search),
    staleTime: 5 * 60_000,
    placeholderData: keepPreviousData,
  });
}

export function useResearchSources(symbol: string | undefined) {
  return useQuery({
    queryKey: ["research-sources", symbol],
    queryFn: () => research.getResearchSources(symbol!),
    enabled: Boolean(symbol),
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function useResearchHistory(enabled: boolean, symbol?: string) {
  return useQuery({
    queryKey: ["research-history", symbol ?? ""],
    queryFn: () => research.getResearchHistory(symbol),
    enabled,
    staleTime: 0, // always fresh when the drawer opens
  });
}

/* --------------------------- Company terminal --------------------------- */

export function useHistoryRange(symbol: string | undefined, range: string, enabled: boolean) {
  return useQuery({
    queryKey: ["stock-history", symbol, range],
    queryFn: () => services.getStockHistory(symbol!, range),
    enabled: Boolean(symbol) && enabled,
    staleTime: 30 * 60_000, // long-range daily bars rarely change
    retry: false,
  });
}

export function useStatements(symbol: string | undefined) {
  return useQuery({
    queryKey: ["statements", symbol],
    queryFn: () => services.getStatements(symbol!),
    enabled: Boolean(symbol),
    staleTime: 30 * 60_000,
    retry: false,
  });
}

export function useRatios(symbol: string | undefined) {
  return useQuery({
    queryKey: ["ratios", symbol],
    queryFn: () => services.getRatios(symbol!),
    enabled: Boolean(symbol),
    staleTime: 30 * 60_000,
    retry: false,
  });
}

export function useCagr(symbol: string | undefined) {
  return useQuery({
    queryKey: ["cagr", symbol],
    queryFn: () => services.getCagr(symbol!),
    enabled: Boolean(symbol),
    staleTime: 30 * 60_000,
    retry: false,
  });
}

export function useProsCons(symbol: string | undefined) {
  return useQuery({
    queryKey: ["pros-cons", symbol],
    queryFn: () => services.getProsCons(symbol!),
    enabled: Boolean(symbol),
    staleTime: 60 * 60_000,
    retry: false,
  });
}

export function useRefreshProsCons() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => services.getProsCons(symbol, true),
    onSuccess: (data, symbol) => qc.setQueryData(["pros-cons", symbol], data),
  });
}

/* ------------------------ Sentiment Intelligence ------------------------ */

export function useSentiment(symbol: string | undefined) {
  return useQuery({
    queryKey: ["sentiment", symbol],
    queryFn: () => services.getSentiment(symbol!),
    enabled: Boolean(symbol),
    staleTime: 10 * 60_000, // matches the server-side cache TTL
    retry: false,
  });
}

export function useSentimentHistory(symbol: string | undefined) {
  return useQuery({
    queryKey: ["sentiment-history", symbol],
    queryFn: () => services.getSentimentHistory(symbol!),
    enabled: Boolean(symbol),
    staleTime: 10 * 60_000,
    retry: false,
  });
}

export function useRecomputeSentiment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => services.recomputeSentiment(symbol),
    onSuccess: (data, symbol) => {
      qc.setQueryData(["sentiment", symbol], data);
      qc.invalidateQueries({ queryKey: ["sentiment-history", symbol] });
    },
  });
}

/* ----------------------------- Watchlist ----------------------------- */

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: services.getWatchlist,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export function useWatchMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["watchlist"] });
  const add = useMutation({ mutationFn: ({ symbol, note }: { symbol: string; note?: string }) => services.addWatch(symbol, note), onSuccess: invalidate });
  const remove = useMutation({ mutationFn: (symbol: string) => services.removeWatch(symbol), onSuccess: invalidate });
  return { add, remove };
}

export function useAlertRules(symbol?: string) {
  return useQuery({
    queryKey: ["alert-rules", symbol ?? ""],
    queryFn: () => services.getAlertRules(symbol),
    staleTime: 30_000,
  });
}

export function useAlertRuleMutations() {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["alert-rules"] });
    qc.invalidateQueries({ queryKey: ["watchlist"] });
  };
  const create = useMutation({ mutationFn: services.createAlertRule, onSuccess: invalidate });
  const remove = useMutation({ mutationFn: (id: number) => services.deleteAlertRule(id), onSuccess: invalidate });
  return { create, remove };
}

export function useAlertEvents() {
  return useQuery({
    queryKey: ["alert-events"],
    queryFn: services.getAlertEvents,
    staleTime: 30_000,
    refetchInterval: 60_000, // keeps the bell badge fresh
  });
}

export function useUsage() {
  return useQuery({
    queryKey: ["usage"],
    queryFn: authApi.fetchUsage,
    staleTime: 30_000,
  });
}

export function useMarkAlertsSeen() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: services.markAlertEventsSeen,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alert-events"] }),
  });
}
