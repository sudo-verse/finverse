import { apiClient } from "./client";
import type {
  AIReport,
  AlertEvent,
  AlertKind,
  AlertRule,
  Announcement,
  AnnouncementFeedRow,
  AnnualReportFile,
  BrsrFile,
  Company,
  CompanyProfile,
  CompetitorAnalysis,
  CorpAction,
  CorpEvent,
  DashboardData,
  HoldingCreate,
  IndexQuote,
  IntradaySeries,
  LiveQuote,
  CagrRow,
  CorporateEventRow,
  DealRow,
  EarningsRow,
  InsiderTrade,
  MarketFlowSummary,
  SastRow,
  ConvictionRow,
  TechnicalsOut,
  TechnicalRow,
  SavedScreen,
  RadarRow,
  SectorPerf,
  StockEarnings,
  StockRange,
  ValuationOut,
  ValuationRow,
  MarketMovers,
  MarketOverview,
  MarqueeItem,
  NsePeer,
  TurnoverRow,
  Paginated,
  PerformanceRow,
  PortfolioData,
  PricePoint,
  ProsCons,
  RatioPoint,
  SentimentData,
  SentimentHistoryPoint,
  StatementRow,
  QuarterlyResult,
  QuarterOption,
  ShareholdingPeriod,
  Signal,
  SignalFacets,
  SignalFilters,
  StockDetail,
  WatchlistItem,
} from "@/types";

export async function getDashboard(): Promise<DashboardData> {
  return (await apiClient.get<DashboardData>("/dashboard")).data;
}

export async function getSignals(filters: SignalFilters): Promise<Paginated<Signal>> {
  const { search, signal, source, sentiment, page = 1, pageSize = 12 } = filters;
  const params = {
    page,
    pageSize,
    search: search?.trim() || undefined,
    signal: signal && signal !== "ALL" ? signal : undefined,
    source: source && source !== "ALL" ? source : undefined,
    sentiment: sentiment && sentiment !== "ALL" ? sentiment : undefined,
  };
  return (await apiClient.get<Paginated<Signal>>("/signals", { params })).data;
}

export async function getSignalFacets(): Promise<SignalFacets> {
  return (await apiClient.get<SignalFacets>("/signals/facets")).data;
}

export async function getStocks(search?: string): Promise<Company[]> {
  return (await apiClient.get<Company[]>("/stocks", { params: { search } })).data;
}

export async function getStock(symbol: string): Promise<StockDetail> {
  return (await apiClient.get<StockDetail>(`/stocks/${symbol}`)).data;
}

export async function getCompetitors(symbol: string): Promise<CompetitorAnalysis> {
  return (await apiClient.get<CompetitorAnalysis>(`/competitors/${symbol}`)).data;
}

export async function getPortfolio(): Promise<PortfolioData> {
  return (await apiClient.get<PortfolioData>("/portfolio")).data;
}

export async function addHolding(payload: HoldingCreate): Promise<void> {
  await apiClient.post("/portfolio/holdings", payload);
}

export async function clearHoldings(): Promise<void> {
  await apiClient.delete("/portfolio/holdings");
}

/* ------------------------------ Live NSE data ------------------------------ */

export async function getLiveQuote(symbol: string): Promise<LiveQuote> {
  return (await apiClient.get<LiveQuote>(`/stocks/${symbol}/live`)).data;
}

export async function getAnnouncements(symbol: string, limit = 10): Promise<Announcement[]> {
  return (await apiClient.get<Announcement[]>(`/stocks/${symbol}/announcements`, { params: { limit } })).data;
}

export async function getCorporateActions(symbol: string, limit = 10): Promise<CorpAction[]> {
  return (await apiClient.get<CorpAction[]>(`/stocks/${symbol}/corporate-actions`, { params: { limit } })).data;
}

export async function getAnnualReports(symbol: string, limit = 10): Promise<AnnualReportFile[]> {
  return (await apiClient.get<AnnualReportFile[]>(`/stocks/${symbol}/annual-reports`, { params: { limit } })).data;
}

export async function getEvents(symbol: string, limit = 5): Promise<CorpEvent[]> {
  return (await apiClient.get<CorpEvent[]>(`/stocks/${symbol}/events`, { params: { limit } })).data;
}

export async function getBoardMeetings(symbol: string, limit = 10): Promise<CorpEvent[]> {
  return (await apiClient.get<CorpEvent[]>(`/stocks/${symbol}/board-meetings`, { params: { limit } })).data;
}

export async function getQuarterlyResults(symbol: string): Promise<QuarterlyResult[]> {
  return (await apiClient.get<QuarterlyResult[]>(`/stocks/${symbol}/results`)).data;
}

export async function getLivePeers(symbol: string, quarter = ""): Promise<NsePeer[]> {
  return (await apiClient.get<NsePeer[]>(`/competitors/${symbol}/live`, { params: { quarter } })).data;
}

export async function getPeerQuarters(symbol: string): Promise<QuarterOption[]> {
  return (await apiClient.get<QuarterOption[]>(`/competitors/${symbol}/quarters`)).data;
}

export async function getMarketOverview(): Promise<MarketOverview> {
  return (await apiClient.get<MarketOverview>("/market/overview")).data;
}

export async function getMarketMovers(): Promise<MarketMovers> {
  return (await apiClient.get<MarketMovers>("/market/movers")).data;
}

export async function getSectors(): Promise<SectorPerf[]> {
  return (await apiClient.get<SectorPerf[]>("/market/sectors")).data;
}

export async function getRadar(band: "high" | "low", threshold = 5, universe?: string): Promise<RadarRow[]> {
  return (await apiClient.get<RadarRow[]>("/market/radar", { params: { band, threshold, limit: 100, universe } })).data;
}

export async function getStockRange(symbol: string): Promise<StockRange> {
  return (await apiClient.get<StockRange>(`/stocks/${symbol}/range-52w`)).data;
}

export async function getMarketFlows(days = 30): Promise<MarketFlowSummary> {
  return (await apiClient.get<MarketFlowSummary>("/market/flows", { params: { days } })).data;
}

export async function getEarningsTracker(
  sort: "pat" | "revenue" | "margin" = "pat",
  limit = 50,
  universe?: string,
): Promise<EarningsRow[]> {
  return (await apiClient.get<EarningsRow[]>("/market/earnings", { params: { sort, limit, universe } })).data;
}

export async function getStockEarnings(symbol: string): Promise<StockEarnings> {
  return (await apiClient.get<StockEarnings>(`/stocks/${symbol}/earnings`)).data;
}

export async function getAnnouncementsFeed(params: {
  category?: string;
  symbol?: string;
  q?: string;
  days?: number;
  routine?: boolean;
  limit?: number;
  universe?: string;
} = {}): Promise<AnnouncementFeedRow[]> {
  return (await apiClient.get<AnnouncementFeedRow[]>("/market/announcements", { params })).data;
}

export async function getSastFeed(params: {
  action?: string;
  symbol?: string;
  promoter?: boolean;
  q?: string;
  days?: number;
  limit?: number;
  universe?: string;
} = {}): Promise<SastRow[]> {
  return (await apiClient.get<SastRow[]>("/market/sast", { params })).data;
}

export async function getStockInsider(symbol: string, limit = 25): Promise<InsiderTrade[]> {
  return (await apiClient.get<InsiderTrade[]>(`/stocks/${symbol}/insider`, { params: { limit } })).data;
}

export async function getValuationLeaderboard(
  verdict?: string,
  limit = 50,
  universe?: string,
): Promise<ValuationRow[]> {
  return (await apiClient.get<ValuationRow[]>("/market/valuation", { params: { verdict, limit, universe } })).data;
}

export async function getStockValuation(symbol: string): Promise<ValuationOut> {
  return (await apiClient.get<ValuationOut>(`/stocks/${symbol}/valuation`)).data;
}

export async function getConvictionLeaderboard(
  order: "top" | "bottom" = "top",
  limit = 60,
  universe?: string,
): Promise<ConvictionRow[]> {
  return (await apiClient.get<ConvictionRow[]>("/market/conviction", { params: { order, limit, universe } })).data;
}

export async function getStockConviction(symbol: string): Promise<ConvictionRow | null> {
  return (await apiClient.get<ConvictionRow | null>(`/stocks/${symbol}/conviction`)).data;
}

export async function getStockTechnicals(symbol: string): Promise<TechnicalsOut | null> {
  return (await apiClient.get<TechnicalsOut | null>(`/stocks/${symbol}/technicals`)).data;
}

export async function getTechnicalScreen(
  signal: "bullish" | "bearish" = "bullish",
  limit = 60,
  universe?: string,
): Promise<TechnicalRow[]> {
  return (await apiClient.get<TechnicalRow[]>("/market/technicals", { params: { signal, limit, universe } })).data;
}

export async function getSavedScreens(): Promise<SavedScreen[]> {
  return (await apiClient.get<SavedScreen[]>("/screens")).data;
}

export async function saveScreen(payload: {
  name: string;
  filters: Record<string, string>;
  industry?: string | null;
  universe?: string | null;
  notify?: boolean;
}): Promise<SavedScreen> {
  return (await apiClient.post<SavedScreen>("/screens", payload)).data;
}

export async function deleteSavedScreen(id: number): Promise<void> {
  await apiClient.delete(`/screens/${id}`);
}

export async function getDeals(params: {
  type?: string;
  side?: string;
  symbol?: string;
  days?: number;
  limit?: number;
  universe?: string;
} = {}): Promise<DealRow[]> {
  return (await apiClient.get<DealRow[]>("/market/deals", { params })).data;
}

export async function getEventsCalendar(params: {
  window?: string;
  type?: string;
  symbol?: string;
  days?: number;
  limit?: number;
} = {}): Promise<CorporateEventRow[]> {
  return (await apiClient.get<CorporateEventRow[]>("/market/events", { params })).data;
}

export async function getAllIndices(): Promise<IndexQuote[]> {
  return (await apiClient.get<IndexQuote[]>("/market/indices")).data;
}

export async function getIndexChart(index: string, flag = "1D"): Promise<IntradaySeries> {
  return (await apiClient.get<IntradaySeries>("/market/index-chart", { params: { index, flag } })).data;
}

export async function getMarquee(): Promise<MarqueeItem[]> {
  return (await apiClient.get<MarqueeItem[]>("/market/marquee")).data;
}

export async function getTurnover(): Promise<TurnoverRow[]> {
  return (await apiClient.get<TurnoverRow[]>("/market/turnover")).data;
}

export async function getIntraday(symbol: string, days = "1D"): Promise<IntradaySeries> {
  return (await apiClient.get<IntradaySeries>(`/stocks/${symbol}/intraday`, { params: { days } })).data;
}

export async function getShareholding(symbol: string): Promise<ShareholdingPeriod[]> {
  return (await apiClient.get<ShareholdingPeriod[]>(`/stocks/${symbol}/shareholding`)).data;
}

export async function getPerformance(symbol: string): Promise<PerformanceRow[]> {
  return (await apiClient.get<PerformanceRow[]>(`/stocks/${symbol}/performance`)).data;
}

export async function getProfile(symbol: string): Promise<CompanyProfile> {
  return (await apiClient.get<CompanyProfile>(`/stocks/${symbol}/profile`)).data;
}

export async function getBrsr(symbol: string): Promise<BrsrFile[]> {
  return (await apiClient.get<BrsrFile[]>(`/stocks/${symbol}/brsr`)).data;
}

export async function generateReport(symbol: string, useCache = true): Promise<AIReport> {
  return (await apiClient.post<AIReport>("/report", { symbol, useCache })).data;
}

/* --------------------------- Company terminal --------------------------- */

export async function getStockHistory(symbol: string, range: string): Promise<PricePoint[]> {
  return (await apiClient.get<PricePoint[]>(`/stocks/${symbol}/history`, { params: { range } })).data;
}

export async function getStatements(symbol: string): Promise<StatementRow[]> {
  return (await apiClient.get<StatementRow[]>(`/stocks/${symbol}/statements`)).data;
}

export async function getRatios(symbol: string): Promise<RatioPoint[]> {
  return (await apiClient.get<RatioPoint[]>(`/stocks/${symbol}/ratios`)).data;
}

export async function getCagr(symbol: string): Promise<CagrRow[]> {
  return (await apiClient.get<CagrRow[]>(`/stocks/${symbol}/cagr`)).data;
}

export async function getProsCons(symbol: string, refresh = false): Promise<ProsCons> {
  return (await apiClient.get<ProsCons>(`/stocks/${symbol}/pros-cons`, { params: { refresh } })).data;
}

/* ------------------------ Sentiment Intelligence ------------------------ */

export async function getSentiment(symbol: string): Promise<SentimentData> {
  return (await apiClient.get<SentimentData>(`/sentiment/${symbol}`)).data;
}

export async function getSentimentHistory(symbol: string): Promise<SentimentHistoryPoint[]> {
  return (await apiClient.get<SentimentHistoryPoint[]>(`/sentiment/history/${symbol}`)).data;
}

export async function recomputeSentiment(symbol: string): Promise<SentimentData> {
  return (await apiClient.post<SentimentData>(`/sentiment/recompute/${symbol}`)).data;
}

/* ----------------------------- Watchlist ----------------------------- */

export async function getWatchlist(): Promise<WatchlistItem[]> {
  return (await apiClient.get<WatchlistItem[]>("/watchlist")).data;
}

export async function addWatch(symbol: string, note?: string): Promise<void> {
  await apiClient.post("/watchlist", { symbol, note });
}

export async function removeWatch(symbol: string): Promise<void> {
  await apiClient.delete(`/watchlist/${symbol}`);
}

export async function getAlertRules(symbol?: string): Promise<AlertRule[]> {
  return (await apiClient.get<AlertRule[]>("/alerts", { params: { symbol } })).data;
}

export async function createAlertRule(payload: { symbol: string; kind: AlertKind; threshold?: number | null }): Promise<AlertRule> {
  return (await apiClient.post<AlertRule>("/alerts", payload)).data;
}

export async function deleteAlertRule(id: number): Promise<void> {
  await apiClient.delete(`/alerts/${id}`);
}

export async function getAlertEvents(): Promise<AlertEvent[]> {
  return (await apiClient.get<AlertEvent[]>("/alerts/events")).data;
}

export async function markAlertEventsSeen(): Promise<void> {
  await apiClient.post("/alerts/events/seen");
}
