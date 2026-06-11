/* TypeScript mirrors of the FastAPI response schemas (backend/schemas/*).
   All fields are camelCase — the backend serializes with a camelCase alias
   generator, so these map 1:1 to the live API. */

/* ---------------------------------- Signals -------------------------------- */

export type SignalType = "BUY" | "SELL" | "HOLD";
export type Sentiment = "positive" | "negative" | "neutral";

export interface Signal {
  id: number;
  symbol: string | null;
  companyName: string | null;
  signal: string;
  confidence: number | null; // engine sentiment_score (0–1)
  sentiment: string | null;
  eventType: string | null;
  eventTitle: string | null;
  source: string | null;
  price: number | null;
  publishedAt: string | null;
  timestamp: string | null; // ISO (created_at)
}

export interface SignalFacets {
  signals: string[];
  sources: string[];
  sentiments: string[];
}

export interface SignalFilters {
  search?: string;
  signal?: string | "ALL";
  source?: string | "ALL";
  sentiment?: string | "ALL";
  page?: number;
  pageSize?: number;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/* -------------------------------- Dashboard -------------------------------- */

export interface NewsEvent {
  id: number;
  symbol: string | null;
  headline: string | null;
  source: string | null;
  sentiment: string | null;
  timestamp: string | null;
}

export interface DashboardData {
  metrics: {
    totalCompanies: number;
    totalSignals: number;
    buySignals: number;
    sellSignals: number;
    holdSignals: number;
    priceRows: number;
    portfolioValue: number | null;
    portfolioDayChangePct: number | null;
  };
  signalDistribution: { name: string; value: number }[];
  industryDistribution: { industry: string; count: number }[];
  dailySignalTrend: { date: string; buy: number; sell: number; hold: number }[];
  recentSignals: Signal[];
  recentNews: NewsEvent[];
}

/* ---------------------------------- Stocks --------------------------------- */

export interface Company {
  symbol: string;
  name: string;
  industry: string | null;
  sector: string | null;
  isin?: string | null;
}

export interface PricePoint {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  sma20: number | null;
  sma50: number | null;
  sma200: number | null;
}

export interface QuantMetrics {
  dataPoints: number;
  latestPrice: number | null;
  cumulativeReturn: number | null; // fraction, e.g. 0.12 = +12%
  annualizedReturn: number | null;
  annualizedVolatility: number | null;
  sharpeRatio: number | null;
  maxDrawdown: number | null;
  trend: string | null;
  sma20: number | null;
  sma50: number | null;
  sma200: number | null;
}

export interface Fundamentals {
  period: string | null;
  revenueGrowth: number | null; // fractions
  earningsGrowth: number | null;
  netProfitMargin: number | null;
  roe: number | null;
  roce: number | null;
  debtToEquity: number | null;
  peRatio: number | null;
  pbRatio: number | null;
  eps: number | null;
}

export interface StockDetail {
  symbol: string;
  name: string;
  industry: string | null;
  price: number | null;
  change: number | null;
  changePct: number | null; // fraction
  dayHigh: number | null;
  dayLow: number | null;
  week52High: number | null;
  week52Low: number | null;
  recommendation: string;
  recommendationConfidence: number | null;
  quant: QuantMetrics | null;
  fundamentals: Fundamentals | null;
  priceHistory: PricePoint[];
  recentSignals: Signal[];
}

/* ------------------------------- Competitors ------------------------------- */

export interface PeerRow {
  symbol: string;
  company: string | null;
  revenueGrowth: number | null;
  earningsGrowth: number | null;
  netProfitMargin: number | null;
  roe: number | null;
  roce: number | null;
  debtToEquity: number | null;
  peRatio: number | null;
  pbRatio: number | null;
  cumulativeReturn: number | null;
  annualizedVolatility: number | null;
  sharpeRatio: number | null;
}

export interface MetricComparison {
  metric: string;
  value: number | null;
  peerAvg: number | null;
  rank: number | null; // 1 = best
  outOf: number;
}

export interface CompetitorAnalysis {
  symbol: string;
  company: string | null;
  industry: string;
  peerCount: number;
  overallRank: number | null;
  peers: PeerRow[];
  comparison: MetricComparison[];
}

/* --------------------------------- Portfolio ------------------------------- */

export interface Holding {
  symbol: string;
  industry: string | null;
  quantity: number;
  avgPrice: number | null;
  price: number | null;
  value: number | null;
  cost: number | null;
  pnl: number | null;
  pnlPct: number | null; // fraction
  weight: number | null; // fraction
  dayChangePct: number | null; // fraction
}

export interface SectorAllocation {
  sector: string;
  weight: number; // fraction
  value: number | null;
}

export interface PortfolioSummary {
  totalValue: number;
  totalCost: number | null;
  totalPnl: number | null;
  totalPnlPct: number | null;
  dayPnl: number | null;
  dayPnlPct: number | null;
  numHoldings: number;
  numSectors: number;
  hhi: number | null;
  effectiveHoldings: number | null;
  topConcentration: number | null;
  annualizedVolatility: number | null;
  annualizedReturn: number | null;
  sharpeRatio: number | null;
}

export interface GrowthPoint {
  date: string;
  value: number;
  invested: number | null;
}

export interface PortfolioData {
  summary: PortfolioSummary;
  holdings: Holding[];
  sectorAllocation: SectorAllocation[];
  growth: GrowthPoint[];
}

export interface HoldingCreate {
  symbol: string;
  quantity: number;
  avgPrice?: number | null;
}

/* --------------------------------- Live NSE -------------------------------- */

export interface LiveQuote {
  symbol: string;
  companyName: string | null;
  isin: string | null;
  lastPrice: number | null;
  change: number | null;
  pChange: number | null; // percent, e.g. -0.83
  open: number | null;
  dayHigh: number | null;
  dayLow: number | null;
  previousClose: number | null;
  averagePrice: number | null; // VWAP
  totalTradedVolume: number | null;
  totalTradedValue: number | null;
  marketCap: number | null;
  freeFloatMarketCap: number | null;
  issuedSize: number | null;
  faceValue: number | null;
  deliveryToTraded: number | null;
}

export interface Announcement {
  subject: string | null;
  details: string | null;
  attachmentUrl: string | null;
  broadcastAt: string | null;
  industry: string | null;
}

export interface CorpAction {
  subject: string | null;
  exDate: string | null;
  recordDate: string | null;
  series: string | null;
  faceValue: string | null;
}

export interface AnnualReportFile {
  companyName: string | null;
  fromYear: string | null;
  toYear: string | null;
  broadcastAt: string | null;
  fileUrl: string | null;
  fileSize: string | null;
}

export interface CorpEvent {
  date: string | null;
  purpose: string | null;
  description: string | null;
  attachmentUrl: string | null;
  announcedAt: string | null;
}

export interface QuarterlyResult {
  period: string | null;
  toDate: string | null;
  audited: string | null;
  totalIncome: number | null; // ₹ Lakhs
  profitBeforeTax: number | null;
  netProfit: number | null;
  eps: number | null;
  broadcastAt: string | null;
}

export interface NsePeer {
  symbol: string;
  lastPrice: number | null;
  pChange: number | null; // percent
  marketCap: number | null; // ₹
  pe: number | null;
  eps: number | null;
  netProfit: number | null; // ₹ Lakhs
  totalIncome: number | null; // ₹ Lakhs
  debtToEquity: number | null;
  promoterHolding: number | null; // percent
  volume: number | null;
  tradedValue: number | null;
}

export interface IndexQuote {
  name: string;
  last: number | null;
  percChange: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  previousClose: number | null;
  yearHigh: number | null;
  yearLow: number | null;
  time: string | null;
}

export interface GiftNiftyQuote {
  lastPrice: number | null;
  dayChange: number | null;
  perChange: number | null;
  expiry: string | null;
  time: string | null;
}

export interface UsdInrQuote {
  ltp: number | null;
  updatedTime: string | null;
  expiry: string | null;
}

export interface MarketOverview {
  indices: IndexQuote[];
  giftNifty: GiftNiftyQuote | null;
  usdInr: UsdInrQuote | null;
  totalMarketCapLacCr: number | null;
  marketStatus: string | null;
}

export interface Mover {
  symbol: string;
  lastPrice: number | null;
  change: number | null;
  pChange: number | null;
  previousClose: number | null;
  tradedVolume: number | null;
  tradedValue: number | null;
}

export interface MarketMovers {
  gainers: Mover[];
  losers: Mover[];
  mostActive: Mover[];
  timestamp: string | null;
}

export interface IntradayPoint {
  time: number; // epoch ms
  price: number;
}

export interface IntradaySeries {
  symbol: string;
  points: IntradayPoint[];
}

export interface HoldingCategory {
  category: string;
  pct: number | null;
}

export interface ShareholdingPeriod {
  date: string;
  holdings: HoldingCategory[];
}

export interface PerformanceRow {
  period: string;
  stock: number | null; // percent
  index: number | null; // percent
}

export interface CompanyProfile {
  symbol: string;
  companyName: string | null;
  isin: string | null;
  activeSeries: string[];
  isFno: boolean;
  isSlb: boolean;
  isEtf: boolean;
  isSuspended: boolean;
  listingStatus: string | null;
  indices: string[];
  about: string | null;
}

export interface BrsrFile {
  fyFrom: string | null;
  fyTo: string | null;
  attachmentUrl: string | null;
  fileSize: string | null;
  submittedAt: string | null;
}

export interface QuarterOption {
  label: string;
  value: string;
}

export interface MarqueeItem {
  symbol: string;
  lastPrice: number | null;
  change: number | null;
  perChange: number | null;
}

export interface TurnoverRow {
  segment: string | null;
  instrument: string | null;
  turnover: number | null;
  trades: number | null;
  volume: number | null;
  prevTurnover: number | null;
  timestamp: string | null;
}

/* ----------------------------------- GenAI --------------------------------- */

export interface AIReport {
  symbol: string;
  reportMd: string;
  model: string | null;
  generatedAt: string | null;
  cached: boolean;
}

export interface ChatSource {
  source: string;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: ChatSource[];
}

/* ------------------------- AI Research Copilot ------------------------- */

export interface SourceCitation {
  id: string;
  label: string; // "Annual Report 2024, page 128"
  source: string;
  docType: string | null;
  year: number | null;
  page: number | null;
  symbol: string | null; // set in compare mode
  snippet: string;
}

export interface ResearchMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: SourceCitation[];
  followUps?: string[];
  streaming?: boolean;
  error?: boolean;
}

export interface ResearchCompany {
  symbol: string;
  name: string;
  industry: string | null;
  indexedChunks: number;
}

export interface DocTypeSummary {
  docType: string;
  label: string;
  documents: number;
  chunks: number;
  years: number[];
}

export interface CompanySources {
  symbol: string;
  name: string;
  totalChunks: number;
  docTypes: DocTypeSummary[];
  hasFinancials: boolean;
  hasPriceHistory: boolean;
  newsSignals: number;
}

export interface ResearchHistoryItem {
  id: number;
  symbol: string | null;
  mode: "chat" | "compare";
  question: string;
  answer: string | null;
  sources: SourceCitation[];
  createdAt: string;
}

/* --------------------------- Company terminal --------------------------- */

export interface StatementRow {
  period: string;
  revenue: number | null;
  netIncome: number | null;
  ebit: number | null;
  eps: number | null;
  totalAssets: number | null;
  totalEquity: number | null;
  totalLiabilities: number | null;
  operatingCashFlow: number | null;
  revenueGrowth: number | null;
  netIncomeGrowth: number | null;
  epsGrowth: number | null;
}

export interface RatioPoint {
  period: string;
  roe: number | null;
  roce: number | null;
  opm: number | null;
  npm: number | null;
  debtToEquity: number | null;
}

export interface CagrRow {
  metric: string;
  y1: number | null;
  y3: number | null;
  y5: number | null;
  y10: number | null;
}

export interface ProsConsItem {
  point: string;
  confidence: number;
}

export interface ProsCons {
  symbol: string;
  pros: ProsConsItem[];
  cons: ProsConsItem[];
  model: string | null;
  generatedAt: string | null;
  cached: boolean;
}

/* ------------------------ Sentiment Intelligence ------------------------ */

export interface SentimentFactor {
  name: string;
  value: number | null;
  score: number | null;
  status: string;
  explanation: string | null;
}

export interface PillarDetail {
  name: string;
  score: number | null;
  status: string;
  summary: string;
  factors: SentimentFactor[];
}

export interface MomentumRange {
  period: string;
  low: number;
  high: number;
  current: number;
  change: number;
}

export interface PivotLevels {
  pivot: number;
  r1: number;
  r2: number;
  r3: number;
  s1: number;
  s2: number;
  s3: number;
}

export interface NewsBucket {
  positivePct: number;
  negativePct: number;
  neutralPct: number;
  impact: number | null;
  count: number;
}

export interface OwnershipRow {
  category: string;
  pct: number | null;
  delta: number | null;
}

export interface SentimentData {
  symbol: string;
  overall: number;
  recommendation: string;
  confidence: number;
  pillars: PillarDetail[];
  reasons: string[];
  risks: string[];
  momentum: MomentumRange[];
  pivots: PivotLevels | null;
  movingAverages: Record<string, number | null>;
  newsBucket: NewsBucket;
  holdings: OwnershipRow[];
}

export interface SentimentHistoryPoint {
  date: string;
  overall: number | null;
  technical: number | null;
  fundamental: number | null;
  news: number | null;
  ownership: number | null;
  market: number | null;
  recommendation: string | null;
  reason: string | null;
}
