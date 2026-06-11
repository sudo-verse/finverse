# Finverse × Screener.in — Gap Analysis & Roadmap

Audit date: 2026-06-11. Scope: the 11-phase "professional equity research
platform" spec, measured against what Finverse already ships.

Legend: ✅ implemented · 🟡 partial · ❌ missing · 🔌 needs backend · 🗄️ needs new data/tables

## Phase-by-phase

| # | Phase | Status | Notes |
|---|-------|--------|-------|
| 1 | Company Detail Terminal | ✅ mostly | `/stocks/:symbol` has live quote header (price, change, M.Cap, 52W), industry, engine signal, quant+fundamental tiles, NSE profile/business summary (NseInsights). **Missing: dividend yield** (no data source yet); "Investment Highlights" served by AI Pros & Cons + AI report. |
| 2 | Advanced Charting | ✅ mostly | 1D (live intraday), 1M/3M/6M/1Y from DB, **3Y/5Y/10Y/MAX via new `/history?range=` endpoint** (yfinance on demand, server-cached), SMA 20/50/200 + volume. ❌ PE/PB/EV-EBITDA historical charts — needs per-day fundamentals history (🗄️ new table + long ETL; low priority). |
| 3 | Financial Statements | 🟡 | Annual P&L/BS/CF summary with YoY growth + CSV export (new `/statements`). Quarterly results come live from NSE (₹ Lakhs) in CorporatePanel. ❌ Full line-item statements (depreciation, interest, tax breakdowns) — yfinance maps only headline items (🗄️ richer source needed, e.g. screener-style scraping or paid API). ⚠️ Values are in the company's *filing currency* (some file in USD). |
| 4 | Ratio Analysis | 🟡 | ROE/ROCE/OPM/NPM/D-E trends per FY (new `/ratios`). ❌ Working-capital days, debtor days, inventory days, cash-conversion cycle — require receivables/inventory/payables line items we don't ingest (🗄️). |
| 5 | Shareholding Analysis | 🟡 | Promoter/FII/DII/Public per quarter live from NSE (`/shareholding`, shown in NseInsights). ❌ Dedicated trend charts + promoter-change alerts (frontend work on existing data), mutual-fund split & shareholder count (NSE pattern lacks them — 🗄️). |
| 6 | Document Center | 🟡 | Annual reports, BRSR, announcements, board meetings, corp actions all downloadable in CorporatePanel; `documents/` corpus + `/documents/...` static serving exist. ❌ A single "Documents" page aggregating categories with search + per-doc AI summary (🔌 one endpoint reusing `research.retrieve` + Gemini). Credit ratings not integrated (NSE has an endpoint — 🔌). |
| 7 | AI Insights Engine | ❌ | Page not built. Foundation is ready: `research.retrieve()` returns source/page metadata, `company_insights` table caches AI output, pros/cons proves the confidence-score pattern. 🔌 `GET /stocks/{symbol}/insights` generating themed insights (guidance, capacity, risks…) with `{source, page, confidence}`. Quality depends on ingested filings (only news signals indexed by default). |
| 8 | Peer Comparison | 🟡 | Live NSE peers + quarter selector, industry ranking (#rank of N, metric ranks vs peer avg) exist. ❌ Radar chart, sector-median row, composite peer score, market-share comparison (market share needs segment data — 🗄️; rest is frontend + small additions to `competitor_service`). |
| 9 | Pros & Cons | ✅ | New: AI-generated, confidence-scored, grounded in metrics/fundamentals/peers/signals, cached in `company_insights`, regenerate button. |
| 10 | CAGR Analysis | ✅ | New: Sales/Profit/EPS/ROE/Price × 1/3/5/10Y cards (`/cagr`). 5Y/10Y fundamentals show "—" until more annual history exists (yfinance gives ~4 FYs; price CAGR covers all horizons via yfinance MAX). |
| 11 | Research Copilot | ✅ | Built previously: company-aware chat, doc+page citations, compare mode, streaming, history. New this round: Bull Case / Bear Case / DCF Assumptions templates (SWOT, thesis, risks already existed). Transcript citations work once transcripts are dropped in `documents/<SYM>/earnings_calls/`. |

## Data reality (the real constraint)

- `financial_statements`: yfinance backfill running for all 500 companies
  (~4 annual periods each). Quarterly fundamentals: ❌ not in yfinance for
  most NSE names → quarterly view stays NSE-results-based.
- Price history DB = 1 year; longer ranges fetched live from yfinance and
  cached in memory (1 h TTL).
- No source yet for: dividend yield, shareholder count, MF holdings,
  segment/market-share data, debtor/inventory days inputs.

## Priority order (next steps)

1. **Shareholding trends + promoter-change detection** — data already flows; pure frontend. High impact, low effort.
2. **Documents page** — aggregate existing NSE file endpoints + AI summary via the research pipeline. High impact, medium effort.
3. **AI Insights page** (Phase 7) — reuse `research.retrieve` + `company_insights`; needs filings ingested to shine.
4. **Peer radar + composite score** — frontend + small `competitor_service` addition.
5. **Credit ratings** — add NSE corporate-rating NextApi call to `nse_client`.
6. **Valuation history charts (PE/PB)** — needs daily-fundamentals table; build only if genuinely needed.

## New backend surface added in this round

```
GET /api/stocks/{symbol}/history?range=1M|6M|1Y|3Y|5Y|10Y|MAX
GET /api/stocks/{symbol}/statements      # annual, with YoY growth
GET /api/stocks/{symbol}/ratios          # ROE/ROCE/OPM/NPM/D-E per FY
GET /api/stocks/{symbol}/cagr            # Sales/Profit/EPS/ROE/Price × 1/3/5/10Y
GET /api/stocks/{symbol}/pros-cons[?refresh=true]   # AI, cached
```

DB change: `company_insights` table (symbol, kind, content JSON, model,
generated_at) — shared cache for pros/cons and the future insights engine.
