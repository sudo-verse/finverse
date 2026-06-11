# FINVERSE — Complete Technical Handbook

> AI-powered equity research & market-intelligence terminal for NSE India.
> React 19 · FastAPI · SQLAlchemy · FinBERT · Gemini · ChromaDB
>
> This handbook is a System Design Document, Architecture Reference,
> Developer Guide, and Interview Preparation Guide in one. It reflects the
> actual implementation as of 2026-06-11 (commit `7e42b53`).

---

## Table of Contents

1.  [Project Overview](#section-1--project-overview)
2.  [High-Level Architecture](#section-2--high-level-architecture)
3.  [Complete Folder Structure](#section-3--complete-folder-structure)
4.  [File-by-File Reference](#section-4--file-by-file-reference)
5.  [Function-by-Function Analysis](#section-5--function-by-function-analysis)
6.  [Database Design](#section-6--database-design)
7.  [Data Pipeline (ETL)](#section-7--data-pipeline-etl)
8.  [NLP Pipeline](#section-8--nlp-pipeline)
9.  [Signal Engine](#section-9--signal-engine)
10. [Analytics Engine](#section-10--analytics-engine)
11. [AI Research Copilot](#section-11--ai-research-copilot)
12. [Sentiment Intelligence Engine](#section-12--sentiment-intelligence-engine)
13. [API Documentation](#section-13--api-documentation)
14. [Frontend Architecture](#section-14--frontend-architecture)
15. [End-to-End Workflows](#section-15--end-to-end-workflows)
16. [System Design Discussion](#section-16--system-design-discussion)
17. [Scalability Analysis](#section-17--scalability-analysis)
18. [Security Analysis](#section-18--security-analysis)
19. [Interview Guide](#section-19--interview-guide)
20. [Project Introductions](#section-20--project-introductions)
21. [Resume Descriptions](#section-21--resume-descriptions)
22. [Project Story](#section-22--project-story)
23. [Future Roadmap](#section-23--future-roadmap)
24. [Appendix: Diagrams & Cheat Sheets](#appendix--diagrams--cheat-sheets)

---

# SECTION 1 — PROJECT OVERVIEW

## 1.1 What Finverse Is

Finverse is a **full-stack equity research and market-intelligence platform
for NSE-listed Indian stocks** — a self-hosted hybrid of Screener.in
(fundamentals), TickerTape (screening), TradingView (charting), Bloomberg
Terminal (live market board), and a ChatGPT-style **AI Research Copilot**
grounded in real company filings.

It runs as three cooperating layers:

1. **A real-time intelligence engine** that polls four news sources
   (NSE announcements, Google News, Moneycontrol, Economic Times) every 60
   seconds, scores each headline with FinBERT sentiment + regex event
   classification, and emits explainable BUY/SELL/HOLD signals with Telegram
   alerts.
2. **A FastAPI analytics backend** exposing ~60 REST endpoints over a
   SQLAlchemy database (500 companies, OHLCV history, annual financials),
   live NSE NextApi data (quotes, shareholding, corporate filings), a
   5-pillar Sentiment Intelligence scorer, a screener, watchlist alerts,
   and signal backtesting.
3. **A React 19 terminal-style frontend** — 12 pages, dark Bloomberg
   aesthetic, live tickers, streaming AI chat with page-level source
   citations.

## 1.2 Why It Was Built / Problem It Solves

Retail equity research in India is fragmented: prices on one site,
fundamentals on another, filings as raw PDFs on NSE, news scattered
everywhere, and zero explainability in "buy/sell" tips. Finverse unifies
**data → analytics → AI reasoning → action (alerts/watchlists)** in one
self-hosted product, and every AI output is *grounded*: signals cite the
triggering headline, sentiment scores decompose into factor-level
explanations, and copilot answers cite the annual-report page they came
from.

## 1.3 Target Users

| User | What they get |
| --- | --- |
| Retail investor | One terminal: live quotes, fundamentals, signals, alerts |
| Analyst / student | Screener, peer ranking, ratio trends, CAGR, exportable data |
| AI-curious developer | Production-shaped RAG + scoring reference implementation |

## 1.4 Pitch by Audience

**Investor pitch:** "Bloomberg costs $25k/seat. Finverse delivers the daily
workflow of a retail Indian equity analyst — live market data, fundamental
screening, explainable AI signals, and filing-grounded research chat — on a
single self-hosted box with free-tier AI."

**Recruiter pitch:** "A solo-built, end-to-end product: 100+ Python modules,
~60 REST endpoints, 14 SQLAlchemy tables, a React 19 TypeScript frontend,
a streaming RAG pipeline with hybrid retrieval + reranking, an ML scoring
engine with a pytest suite that caught real bugs, background workers,
schedulers, and a real-time news pipeline."

**Software-engineer pitch:** "Layered monolith: ingestion → NLP → engine →
DB → API → UI. Sync FastAPI on a threadpool over blocking SQLAlchemy/pandas;
camelCase Pydantic schemas mirrored 1:1 by TypeScript types; SSE streaming
for LLM tokens; ChromaDB vector store with metadata-filtered hybrid search;
three daemon workers (news, alerts, ETL) inside the API process."

**Product-manager pitch:** "The loop is discover (screener/dashboard) →
research (terminal + copilot) → decide (sentiment + signals) → act
(watchlist/alerts/portfolio) → learn (signal backtesting). Every feature
feeds the next stage of that loop."

## 1.5 Key Differentiators

1. **Explainability everywhere** — signals carry the headline + event +
   sentiment that caused them; sentiment scores decompose into ~15 scored
   factors with natural-language reasons; copilot answers carry `[n]`
   citations resolvable to "Annual Report 2025, page 128" with a link to
   the PDF page.
2. **Honest measurement** — a built-in backtester reports whether the
   engine's own signals actually made money (hit rate, forward 7d/30d
   returns).
3. **Self-healing data layer** — NSE cookie-handshake retry, stale-cache
   serving on upstream failure, rate-limit-aware Gemini embedding,
   ETL catch-up runs after downtime.
4. **Zero-ops** — the news engine, alert evaluator, and daily ETL run as
   daemon threads inside the API process; one `uvicorn` command boots the
   entire platform.

---

# SECTION 2 — HIGH-LEVEL ARCHITECTURE

## 2.1 System Diagram

```
                                   ┌─────────────────────────────────────────┐
                                   │              EXTERNAL WORLD             │
                                   │  NSE NextApi   Yahoo Finance   Gemini   │
                                   │  Google News   Moneycontrol    ET RSS   │
                                   │  HuggingFace(FinBERT)  Telegram Bot API │
                                   └────────┬──────────────┬─────────────────┘
                                            │              │
                  ┌─────────────────────────▼──────────────▼──────────────────┐
                  │                    FASTAPI PROCESS (port 8000)             │
                  │                                                            │
   ┌──────────┐   │  ┌──────────────┐ ┌───────────────┐ ┌──────────────────┐  │
   │ Browser  │   │  │ EngineWorker │ │ AlertWorker   │ │ EtlWorker        │  │
   │ React 19 │   │  │ 60s news     │ │ 300s rule     │ │ daily 18:30 IST  │  │
   │ (5173)   │   │  │ sweep+FinBERT│ │ evaluation    │ │ prices/financials│  │
   └────┬─────┘   │  └──────┬───────┘ └──────┬────────┘ │ +sentiment snaps │  │
        │ /api    │         │                │          └────────┬─────────┘  │
        │ (Vite   │  ┌──────▼────────────────▼───────────────────▼─────────┐  │
        │  proxy) │  │            backend/api  (12 routers, ~60 endpoints) │  │
        ├────────►│  │            backend/services (14 service modules)    │  │
        │  SSE ◄──┤  │            backend/schemas (camelCase Pydantic v2)  │  │
        │         │  └──────┬───────────────────┬──────────────┬──────────┘  │
        │         │         │                   │              │             │
        │         │  ┌──────▼──────┐   ┌────────▼──────┐  ┌────▼──────────┐  │
        │         │  │ app/analytics│  │ app/genai     │  │ app/market    │  │
        │         │  │ metrics,     │  │ RAG, research,│  │ NSEClient     │  │
        │         │  │ technicals,  │  │ reports,      │  │ (cookie       │  │
        │         │  │ portfolio,   │  │ gemini_client │  │  handshake)   │  │
        │         │  │ peers        │  └───────┬───────┘  └───────────────┘  │
        │         │  └──────┬──────┘           │                             │
        │         └─────────┼──────────────────┼─────────────────────────────┘
        │                   │                  │
        │            ┌──────▼──────┐    ┌──────▼──────┐
        │            │  SQLite     │    │  ChromaDB   │
        │            │ finverse.db │    │  chroma_db/ │
        │            │ 14 tables   │    │  embeddings │
        │            └─────────────┘    └─────────────┘
        │
   documents/  ←  NSE filings PDFs (served at /docfiles, indexed into Chroma)
```

## 2.2 Component Responsibilities

| Component | Responsibility |
| --- | --- |
| `frontend/` | Presentation only. No business logic. Talks to `/api` via Axios + TanStack Query; streams SSE via `fetch`. |
| `backend/api` | HTTP shape: routing, validation, status codes. Thin — delegates everything. |
| `backend/services` | Orchestration: compose `app/` modules, cache, map to schemas. |
| `backend/schemas` | Pydantic v2 models; `to_camel` alias generator makes JSON match TS types 1:1; naive datetimes auto-tagged UTC. |
| `backend/core` | Settings (env `BACKEND_`), DB session dependency, domain exceptions, 3 background workers. |
| `app/ingestion` | Fetch + normalize articles from 4 sources. |
| `app/nlp` | FinBERT sentiment (lazy-loaded), spaCy NER. |
| `app/engine` | Event classification, signal generation, explanation, risk, paper trading. |
| `app/analytics` | All quantitative math (returns, Sharpe, RSI, MACD, ratios, peers, portfolio). |
| `app/genai` | Gemini client (text/stream/embed), RAG store, hybrid research pipeline, report generator. |
| `app/etl` | Loaders: companies, prices, financials, signals, documents, NSE filings. |
| `app/db` | Engine/session, 14 ORM models, repository helpers. |
| `app/market` | NSE NextApi client with cookie handshake + retry; Yahoo fallback price. |

## 2.3 Request / Response Flow

A typical request (`GET /api/stocks/TCS`):

```
Browser ──GET /api/stocks/TCS──► Vite dev proxy ──► uvicorn (FastAPI)
  → log_requests middleware (timing log)
  → router backend/api/stocks.py::get_stock        (sync def → threadpool)
  → Depends(get_db) opens a request-scoped Session
  → stock_service.detail(): loads prices (pandas), computes SMA/quant
    metrics via app.analytics, NaN-safe last close, recent signals
  → returns StockDetailOut (snake_case fields)
  → Pydantic serializes → camelCase JSON, naive datetimes → "...Z"
  → middleware logs "GET /api/stocks/TCS -> 200 (38.2 ms)"
Browser ◄─JSON── TanStack Query caches it (staleTime 60s) → React renders
```

A streaming request (`POST /api/research/chat`) differs: the router returns
a `StreamingResponse` whose generator yields SSE frames (`sources` → many
`delta`s → `done`); the frontend reads it with `fetch` + `ReadableStream`
because Axios cannot stream in browsers.

## 2.4 Data Flow (write side)

```
News sources ─► UnifiedFetcher ─► dedup(uid+title) ─► FinBERT ─► detect_event
   ─► generate_signal ─► save_signal (DB unique-uid upsert + signals.json)
   ─► Telegram (BUY only, only when row was new)

Yahoo Finance ─► prices_etl / financials_etl ─► upserts (company_id, date|period)
NSE filings  ─► fetch_filings ─► documents/<SYM>/ ─► ingest_documents
   ─► chunk → Gemini embed (429-retry) → ChromaDB upsert {symbol, doc_type, year, page}
```

---

# SECTION 3 — COMPLETE FOLDER STRUCTURE

```
ai-stock/
├── app.py                      # Legacy Streamlit dashboard (read-only view)
├── app/                        # Domain engine (framework-free Python)
│   ├── config.py               # .env loader: DATABASE_URL, GEMINI_*, CHROMA_DIR
│   ├── main_nse.py             # Real-time engine: run_cycle() + standalone loop
│   ├── analytics/              # Quant math (pure pandas/numpy)
│   │   ├── metrics.py          #   returns, vol, Sharpe, drawdown, SMA/EMA, trend
│   │   ├── technicals.py       #   RSI, MACD, Bollinger, pivots, momentum, golden cross
│   │   ├── analytics.py        #   load_prices() + per-symbol quant summary
│   │   ├── financial_analysis.py #  ratio computation from financial_statements
│   │   ├── competitor_analysis.py # peer discovery + metric ranking
│   │   └── portfolio.py        #   holdings → value, P&L, weights, sector alloc
│   ├── db/                     # Persistence
│   │   ├── database.py         #   engine, SessionLocal, get_session(), Base
│   │   ├── models.py           #   14 ORM models (see Section 6)
│   │   ├── repository.py       #   upserts, signal/report/research/holding helpers
│   │   └── init_db.py          #   Base.metadata.create_all bootstrap
│   ├── engine/                 # Decision logic
│   │   ├── event.py            #   regex event classifier (orders, results, M&A…)
│   │   ├── signal.py           #   (sentiment, score, event) → BUY/HOLD
│   │   ├── explain.py          #   human-readable decision explanation
│   │   ├── risk.py             #   naive stop-loss/target from price
│   │   ├── backtest.py         #   single-signal price-move evaluation
│   │   └── keyword_engine.py   #   keyword fallback scorer (pre-FinBERT era)
│   ├── etl/                    # Batch loaders (all idempotent upserts)
│   │   ├── run_etl.py          #   orchestrator: companies → prices → signals
│   │   ├── companies_etl.py    #   NIFTY-500 master from NSE CSV
│   │   ├── prices_etl.py       #   OHLCV via yfinance (period param)
│   │   ├── financials_etl.py   #   annual statements via yfinance
│   │   ├── signals_etl.py      #   signals.json → DB backfill
│   │   ├── ingest_documents.py #   documents/ tree → ChromaDB (hash manifest)
│   │   └── fetch_filings.py    #   NSE annual-report PDF downloader + indexer
│   ├── genai/                  # LLM layer
│   │   ├── gemini_client.py    #   generate_text / generate_stream / embed(+429 retry)
│   │   ├── rag.py              #   chunking, page-aware PDF ingest, Chroma store
│   │   ├── research.py         #   hybrid retrieval → rerank → compress → answer
│   │   └── report_generator.py #   structured-data investment report + DB cache
│   ├── ingestion/              # News collectors (one class per source)
│   │   ├── base_fetcher.py     #   make_article() normalizer + BaseFetcher ABC
│   │   ├── nse_fetcher.py      #   NSE corporate announcements
│   │   ├── rss_fetcher.py      #   Google News + Economic Times RSS (HTML-safe)
│   │   ├── moneycontrol_fetcher.py # Moneycontrol news API
│   │   ├── unified_fetcher.py  #   fan-in + cross-source dedup
│   │   ├── article_extractor.py#   full-article text fetch (newspaper-style)
│   │   └── news_fetcher.py     #   legacy Moneycontrol fetcher (superseded)
│   ├── market/                 # Market-data clients
│   │   ├── nse_client.py       #   NSEClient: cookie handshake, quote/next/home APIs
│   │   ├── stock_data.py       #   get_stock_price(): NSE → Yahoo fallback
│   │   └── snapshot.py         #   one-shot OHLC snapshot helper
│   ├── nlp/
│   │   ├── sentiment.py        #   FinBERT pipeline (lazy singleton)
│   │   └── ner.py              #   spaCy ORG entity extraction
│   ├── trading/paper_trading.py#   simulated trades ledger (JSON)
│   └── utils/                  #   logger, fuzzy ticker mapping (rapidfuzz),
│                               #   storage (dedup-gated save), telegram, text cleanup
├── backend/                    # HTTP layer (FastAPI)
│   ├── main.py                 # app factory, middleware, workers, 12 routers
│   ├── core/                   # config, get_db, exceptions, engine.py (3 workers)
│   ├── api/                    # routers: dashboard signals stocks competitors
│   │                           #   portfolio market reports chat research screener
│   │                           #   sentiment watchlist
│   ├── schemas/                # camelCase Pydantic models per domain
│   └── services/               # orchestration per domain (14 modules)
├── frontend/                   # React 19 + Vite 7 + TS + Tailwind v4
│   └── src/
│       ├── api/                # axios client, REST services, SSE research client
│       ├── hooks/              # TanStack Query hooks (one per endpoint family)
│       ├── pages/              # 12 route-level pages (lazy-loaded)
│       ├── components/         # layout/ shared/ ui/ + feature folders
│       ├── lib/                # format.ts (INR/IST/fractions), utils (cn)
│       └── types/index.ts      # TS mirrors of every backend schema
├── documents/                  # Research corpus (PDFs), served at /docfiles
├── tests/                      # pytest: technicals, research helpers, backend logic
├── docs/                       # GAP_ANALYSIS.md, this handbook
├── chroma_db/                  # vector store (gitignored)
└── finverse.db                 # SQLite (gitignored)
```

**Dependency rule:** `frontend → backend → app → (DB/external)`. `app/`
never imports `backend/`; `backend/api` never touches the DB directly
(always through services); the one deliberate exception is
`backend/core/engine.py` workers importing both sides (they orchestrate).

---

# SECTION 4 — FILE-BY-FILE REFERENCE

Format: **Purpose · Key contents · Used by**. (Function-level detail in §5.)

## 4.1 `app/` — Domain Engine

| File | Purpose · Key contents · Used by |
| --- | --- |
| `config.py` | Loads `.env` once. Exposes `DATABASE_URL` (default `sqlite:///finverse.db`), `GEMINI_API_KEY/MODEL/EMBED_MODEL`, `CHROMA_DIR`, Telegram creds. Used by every layer. |
| `main_nse.py` | The real-time engine. `process_article()` (NLP→signal→persist→notify), `run_cycle()` (one sweep, shared with API worker), `run()` (standalone 10s loop), seen-uid persistence in `engine_state.json` (cap 2000). |
| `analytics/metrics.py` | Pure functions on `pd.Series`: `daily_returns`, `cumulative_return`, `annualized_return/volatility`, `sharpe_ratio`, `max_drawdown`, `moving_average(sma|ema)`, `latest_moving_averages`, `detect_trend`, `compute_all`. |
| `analytics/technicals.py` | Sentiment-engine indicators: `rsi` (Wilder), `macd` (with noise-floor crossover), `bollinger` (%B), `moving_average_levels` (SMA/EMA 20-200), `golden_cross`, `pivot_points`, `momentum_ranges` (1W–1Y), `volume_trend`. |
| `analytics/analytics.py` | `load_prices(symbol)` → DataFrame from DB; `analyze_symbol` → quant dict; `analyze_all`. |
| `analytics/financial_analysis.py` | `analyze_symbol` → revenue/earnings growth, NPM, ROE, ROCE, D/E, PE, PB, EPS from `financial_statements`. |
| `analytics/competitor_analysis.py` | `get_peers` (same industry), `compare_symbol` (rank each metric vs peers), `compare_industry` (full table). |
| `analytics/portfolio.py` | `compute_portfolio()` → value, P&L, weights, effective holdings (1/HHI), sector allocation, portfolio vol/Sharpe from weighted daily returns. |
| `db/database.py` | SQLAlchemy engine + `SessionLocal`; `get_session()` commit/rollback context manager. |
| `db/models.py` | 14 ORM models — full reference in §6. |
| `db/repository.py` | `upsert_company/price/financial`, `save_signal_to_db` (uid-dedup, returns bool), AI-report cache, research-chat history, portfolio holdings CRUD. |
| `engine/event.py` | `clean_text`, `CATEGORY_PATTERNS` (ordered regex list: order_win, earnings, agreement_mou, securities_issuance, mgmt_change, ratings, settlement…), `classify_event`, `detect_event`. |
| `engine/signal.py` | `generate_signal(label, score, event)`: BUY iff event∈GOOD_EVENTS ∧ label=positive ∧ score>0.75, else HOLD. Deliberately conservative. |
| `engine/explain.py` | Template explanation: "X shows positive sentiment due to order_win, so signal = BUY". |
| `engine/risk.py` | `risk_management(price)` → ±5% stop-loss/target tuple. |
| `engine/backtest.py` | `evaluate_signal(signal, prev, curr)` → did price move with the signal. |
| `engine/keyword_engine.py` | Legacy keyword scorer + `final_signal` combiner (pre-FinBERT fallback). |
| `etl/*` | See §7. |
| `genai/*` | See §11. |
| `ingestion/*` | See §7.5. `base_fetcher.make_article()` is the canonical article dict: `{source,title,text,company,ticker,url,timestamp,uid}`. |
| `market/nse_client.py` | `NSEClient`: requests.Session + homepage cookie handshake; `get_stock_price` (NIFTY-500 snapshot → Yahoo fallback); `quote_api/next_api/home_api` → `_next_api_get` (200→json, 401/403→re-handshake retry once). |
| `nlp/sentiment.py` | Lazy FinBERT (`ProsusAI/finbert`) singleton; `get_sentiment(text)` → (label, score). Lazy because the API imports the engine but may never run it. |
| `nlp/ner.py` | spaCy `en_core_web_sm`; `extract_companies(text)` → ORG entities. |
| `utils/mapping.py` | rapidfuzz fuzzy match of headline → NIFTY-500 company; `resolve_ticker(text)` → (company, ticker) or (None, None); drives "news without a tradable ticker is noise". |
| `utils/storage.py` | `save_signal(data)` → DB first (uid dedup), JSON append only if new; returns `is_new` so callers gate Telegram. |
| `utils/text.py` | `strip_html`: entity unescape → tag strip → truncation-safe unterminated-tag strip → whitespace collapse. |
| `utils/telegram.py` | `send_telegram(msg)`, `format_signal_msg(...)`. |

## 4.2 `backend/` — HTTP Layer

| File | Purpose |
| --- | --- |
| `main.py` | App factory: lifespan (init_db + start/stop 3 workers), CORS, request-timing middleware, 4 exception handlers (NotFound/NoData→404, ServiceUnavailable→503, fallback→500), `/health`, `/api/engine/status`, `/docfiles` static mount, 12 routers under `/api`. |
| `core/config.py` | `Settings(BaseSettings)` env-prefix `BACKEND_`: cors_origins, page sizes, engine_enabled/interval, alerts_interval, etl_enabled/hour/minute IST. |
| `core/database.py` | `get_db()` FastAPI dependency yielding request-scoped Session (commit on success / rollback on error). |
| `core/exceptions.py` | `NotFoundError`, `NoDataError`, `ServiceUnavailableError`. |
| `core/engine.py` | `EngineWorker` (60s news sweeps), `AlertWorker` (300s rule evaluation), `EtlWorker` (daily 18:30 IST prices, weekly companies+financials, sentiment snapshots, startup catch-up). All daemon threads with `threading.Event` stop + status dicts. |
| `api/*.py` | 12 routers; every endpoint listed in §13. |
| `services/*.py` | One orchestrator per domain; notable: `nse_service` (TTL cache + stale-serve over NSEClient), `sentiment_service` (§12), `research_service` (§11), `screener_service` (set-based universe builder), `watchlist_service` (CRUD + alert evaluator), `backtest_service` (forward returns), `fundamentals_service` (statements/ratios/CAGR/history/pros-cons). |
| `schemas/*.py` | `APIModel` base (camelCase aliases, from_attributes, UTC-tagging wildcard serializer), `Paginated[T]`, per-domain models. |

## 4.3 `frontend/src/` — React App

| Path | Purpose |
| --- | --- |
| `main.tsx` / `App.tsx` | QueryClient + BrowserRouter; 12 lazy routes inside `AppLayout`. |
| `api/client.ts` | Axios instance, baseURL `/api`, 60s timeout. |
| `api/services.ts` | One typed function per REST endpoint. |
| `api/research.ts` | SSE streaming client (`fetch` + ReadableStream frame parser) + research REST calls. |
| `hooks/queries.ts` | ~40 TanStack Query hooks; polling intervals encode data freshness (quotes 30s, signals 60s, fundamentals 30min). |
| `pages/` | dashboard, signals, sentiment, stock-analysis, competitors, portfolio, research, documents, watchlist, screener, assistant, settings. |
| `components/layout/` | sidebar (NAV_ITEMS source of truth), topbar (live ticks + AlertsBell), ticker-tape, command-palette (Ctrl+K), page-header, app-layout. |
| `components/{stock,research,sentiment,signals,dashboard}/` | Feature components (financials-panel, corporate-panel, nse-insights, research chat suite, gauge, performance-card, markets-board). |
| `components/ui/` | 15 shadcn-style Radix primitives. |
| `lib/format.ts` | INR/compact-INR (Cr/L), fraction %, lakhs, IST-pinned dates (24h), timeAgo, stripHtml. |
| `types/index.ts` | TS mirror of every backend schema (camelCase). |

---

# SECTION 5 — FUNCTION-BY-FUNCTION ANALYSIS

Deep walkthroughs for the load-bearing functions; complete signature tables
for everything else. (Complexities are per call; *n* = series length,
*k* = retrieved chunks, *c* = candidate chunks.)

## 5.1 The Real-Time Engine — `app/main_nse.py`

### `process_article(article: dict) -> None`
**Purpose:** turn one normalized article into a persisted, explainable signal.
**Logic walkthrough:**
1. Truncate text to 512 chars (FinBERT token budget guard).
2. Drop if no ticker (mapping already failed upstream).
3. `get_sentiment(text)` → `(label, score)` — FinBERT inference, ~30–80 ms CPU.
4. `detect_event(text)` → regex category (e.g. `order_win`).
5. `generate_signal(label, score, event)` → BUY/HOLD.
6. `get_stock_price(ticker)` — NSE snapshot, Yahoo fallback; may be None.
7. `save_signal({...})` → **returns `is_new`**; if the uid already exists
   (e.g. re-seen after a restart) it returns False and the function exits —
   this gate is what prevents duplicate Telegram alerts.
8. BUY + new → `send_telegram(format_signal_msg(...))`.
**Example:** input title "TCS wins multimillion-euro deal with Canada Life"
→ positive/0.94, `order_win`, BUY, Telegram message, DB row.

### `run_cycle(fetcher, seen_uids, seen_set) -> int`
One sweep: `fetcher.fetch_all()` → filter `uid ∉ seen_set` → `process_article`
each → persist seen-uids (atomic tmp-file replace, capped at 2000) → return
count of new articles. Shared verbatim by the CLI loop (`run()`) and the
API's `EngineWorker` so behavior can't drift between modes.

## 5.2 Quant Metrics — `app/analytics/metrics.py`

| Function | Returns | Formula |
| --- | --- | --- |
| `daily_returns(p)` | Series | `p.pct_change().dropna()` |
| `cumulative_return(p)` | float | `p[-1]/p[0] − 1` |
| `annualized_return(p)` | float | `(1+cum)^(252/n) − 1` |
| `annualized_volatility(p)` | float | `std(daily) · √252` |
| `sharpe_ratio(p, rf)` | float | `(ann_ret − rf) / ann_vol` |
| `max_drawdown(p)` | float | `min(p/cummax(p) − 1)` |
| `moving_average(p, w, kind)` | Series | rolling mean / `ewm(span=w)` |
| `detect_trend(p, 20, 50)` | str | SMA20 vs SMA50 → `uptrend/downtrend/sideways` |
| `compute_all(p)` | dict | all of the above, O(n) each |

## 5.3 Technical Indicators — `app/analytics/technicals.py`

### `rsi(prices, window=14) -> float | None`
Wilder's RSI via `ewm(alpha=1/window)` on clipped gains/losses;
`100 − 100/(1+RS)`; returns 100.0 when avg loss is zero; None if n<15.

### `macd(prices, 12, 26, 9) -> dict | None`
EMA12−EMA26 = MACD line; EMA9 of it = signal; histogram = difference.
**Crossover detection has a noise floor** (`0.05%` of last price): a
crossover within the last 5 bars only counts if `|histogram|` clears the
floor. *Why:* in a constant-slope trend MACD converges, the histogram
hovers at ~0, and raw sign-flips would emit endless fake crossovers — a
real bug the pytest suite caught (a clean uptrend scored "bearish").

### `bollinger / golden_cross / pivot_points / momentum_ranges / volume_trend`
%B = (price−lower)/(upper−lower) on 20-period ±2σ bands (zero-width-safe);
golden/death = SMA50−SMA200 sign flip within lookback; classic floor-trader
pivots P=(H+L+C)/3 with R1–R3/S1–S3 (falls back to close when H/L missing);
momentum = low/high/current per {1W,2W,1M,3M,6M,1Y} window; volume trend =
10d avg ÷ 50d avg.

## 5.4 Hybrid RAG — `app/genai/research.py`

### `retrieve(question, symbol, doc_type, year, k=6) -> list[dict]`
The four-stage pipeline:
1. **Semantic** — embed question (Gemini), Chroma `query` top-18 under a
   `_where()` metadata filter (`{$and:[{symbol},{doc_type},{year}]}`).
2. **Keyword** — `_terms()` extracts ≤4 stopword-free terms;
   `where_document={$or:[{$contains:t}…]}`; lexical score =
   Σ log(1+len(term))·count — longer terms ≈ rarer ≈ heavier.
3. **Fusion** — `_fuse()` reciprocal-rank fusion, score = Σ 1/(60+rank);
   items appearing in both lists win; cap 20 candidates.
4. **Rerank** — one Gemini call returns a JSON index array ordering the
   candidates; defensive parse (regex `\[[\d,\s]*\]`), backfill from fused
   order, full fallback to fused order on any failure.
5. **Compress** — `_compress()` keeps sentences sharing terms with the
   query (± neighbor sentences, "…" gaps), 900-char/chunk budget.
Complexity: O(c·s) string work; cost: 1 embed + 1 rerank LLM call.

### `research_answer(question, symbol, history, structured, …)`
Returns `(sources, token_generator)` — sources are resolved *before*
generation so the API can emit the `sources` SSE frame ahead of tokens.
Prompt = question + last-6-turn history + numbered excerpts (9k-char
budget) + Finverse structured JSON (6k budget, cited `[Finverse data]`);
system prompt enforces the analyst format + `[n]` citations.

### `research_compare(symbols, …)`
Per-symbol `retrieve(k=4)` with continuous source numbering across
companies, comparative system prompt (head-to-head table, verdict).

## 5.5 Sentiment Scoring — `backend/services/sentiment_service.py`
See §12 for full factor math. Key helpers: `_band` (0–100 → STRONG SELL…
STRONG BUY at 20/40/60/80), `_clamp`, `_status` (≥60 bullish, <40 bearish),
`_pillar` (mean of factor scores; None = no data → excluded from composite).

## 5.6 Everything Else (signature tables)

**`app/engine`** — `generate_signal(label,score,event)→str`;
`classify_event(text)→category` (first regex match wins, ordered specific→
generic); `detect_event(desc,attachment)`; `explain_decision(...)→str`;
`risk_management(price)→(stop,target)`; `evaluate_signal(sig,prev,curr)→str`;
`keyword_signal(text)`, `final_signal(...)` (legacy).

**`app/utils`** — `resolve_ticker(text)` → fuzzy-match NIFTY-500 name in
headline via rapidfuzz `extractOne` (threshold-gated) → `(company, ticker)`;
`save_signal(data)→bool`; `strip_html(text)→str`; `send_telegram(msg)`.

**`app/etl`** — `companies_etl.run()`, `prices_etl.run(period,limit,symbols)`,
`financials_etl.run(limit,symbols)`, `signals_etl.run()`,
`ingest_documents(symbol?)→{files,chunks,skipped}`,
`ingest_news_signals(symbol?,limit)`, `infer_year(filename)`,
`fetch_annual_reports(symbol,all_years,index)→int`.

**`app/genai/rag.py`** — `chunk_text(text,1000,150)` (sliding window),
`ingest_text(text,source,symbol,doc_type,year,page)→int` (deterministic-id
upsert), `ingest_pdf` (page-by-page so citations get real page numbers),
`ingest_file`, `get_collection()`, `stats()`, `answer_question(q,symbol,k)`
(simple legacy RAG used by `/api/chat`).

**`app/genai/gemini_client.py`** — `is_configured()`, `generate_text(prompt,
system_instruction,model)`, `generate_stream(...)` (yields text chunks),
`embed(texts)` (batches of 100, 429-retry ×4 with 35s·attempt backoff).

**`backend/services/fundamentals_service.py`** — `statements(session,sym)`
(annual rows + YoY growth, `_growth` guards prev≤0), `ratios` (ROE, ROCE =
EBIT/(assets−current liabilities), OPM=EBIT/rev, NPM, D/E=(liab−CL)/equity),
`cagr` (per-metric `(end/start)^(1/y)−1` from FY-year map + price leg from
cached MAX history), `history(session,sym,range)` (DB ≤1Y, yfinance beyond,
1h in-mem cache, SMA enrichment), `pros_cons` (Gemini strict-JSON, cached in
`company_insights`, `refresh` param).

**`backend/services/backtest_service.py`** — `_forward_return(closes,dates,
sig_date,days)` (bisect to first trading day ≥ signal, last ≤ target;
rejects windows spanning <60% of horizon), `compute_performance(session)`
(per-direction hit rate + avg 7d/30d, best/worst examples, 10-min cache).

**`backend/services/watchlist_service.py`** — watchlist CRUD (+ rule cascade
delete), rules CRUD (kind whitelist, threshold requirement), events list /
mark-seen, `evaluate_all()` (24h cooldown → `_check(rule)` → AlertEvent +
Telegram), `_check` per kind: live-quote compare, sentiment compute,
promoter QoQ pp delta, today's BUY signal lookup.

**`backend/services/screener_service.py`** — `_latest_prices` /
`_latest_sentiment` (grouped max-date subquery joins — 3 queries total, not
500), `_build` (one pass: PE, PB, M.Cap=price×shares, ROE/ROCE/NPM/D-E,
YoY growth), `screen` (10-min cache).

**`backend/core/engine.py`** — `EngineWorker.start/stop/_loop`;
`AlertWorker._loop` (evaluate_all every 300s); `EtlWorker._seconds_until_next_run`
(IST wall-clock math), `_prices_stale` (max date < yesterday), `_run_once`
(weekly = Sunday: companies+financials; daily: prices 1mo + sentiment
snapshots), `_snapshot_sentiment` (watchlist ∪ holdings, force=True).

**Frontend (key functions)** — `streamSSE(path,body,cb,signal)` (frame
parser: split on `\n\n`, dispatch sources/delta/done/error, terminal-frame
tracking so "ended unexpectedly" never double-fires); `sendCore(text,base,
single,duo)` in research page (explicit base/target args so regenerate and
auto-send don't race React state); `formatINRCompact` (₹/K/L/Cr/L-Cr Indian
units); `exportCsv` (Blob + synthetic anchor click).

---

# SECTION 6 — DATABASE DESIGN

## 6.1 ER Diagram

```
 companies 1───* price_history          sentiment_scores   research_chats
     │1                                  (symbol,date) UQ    (chat history)
     ├───* financial_statements
     │1                                  company_insights    watchlist 1──cascade──* alert_rules
     └───* news_signals                  (symbol,kind) UQ                              │1
                                                                                        └───* alert_events
 ai_reports (symbol, cached LLM output)         portfolio_holdings (symbol qty avg_price)
```

## 6.2 Tables

**companies** — master: `id PK`, `symbol UQ idx`, `name`, `industry`,
`isin`, `series`, `created_at`. Parent of prices/financials/signals.

**price_history** — `(company_id FK idx, date idx)` UQ; OHLCV floats,
volume BigInteger. ~250 rows/company/year. Append-mostly via upsert.

**financial_statements** — `(company_id, period, period_type)` UQ;
period `"FY2024"`, type `annual`; revenue, net_income, ebit, total_assets,
total_liabilities, current_liabilities, total_equity, operating_cash_flow,
eps, shares_outstanding. **Currency = filing currency (yfinance)** — ratios
are safe, absolute values labeled carefully in UI.

**news_signals** — engine output: `ticker idx`, `source`, `news (1024)`,
`event`, `sentiment_label/score`, `signal idx`, `price`, `published_at`
(source string), **`uid UQ`** (cross-run dedup backbone), `created_at`.

**ai_reports** — cached Gemini investment reports (symbol, content, model,
generated_at). **company_insights** — `(symbol, kind)` UQ JSON cache
(pros_cons today; insights-engine ready). **research_chats** — copilot
history: symbol ("TCS" or "TCS vs INFY"), mode chat|compare, question,
answer, sources_json. **sentiment_scores** — daily snapshot `(symbol,date)`
UQ: overall + 5 pillar scores + recommendation + confidence; powers history
charts and the screener's sentiment column. **watchlist** — `symbol UQ`,
note. **alert_rules** — symbol, kind (6 values), threshold, active,
last_triggered_at (24h cooldown anchor). **alert_events** — fired alerts:
rule_id FK, symbol, message, `seen` (bell badge), created_at.
**portfolio_holdings** — symbol, quantity, avg_price (weighted-average
blended on re-add).

## 6.3 Conventions

- Timestamps stored **naive UTC** (`datetime.utcnow`); the API's wildcard
  serializer tags them UTC on the way out; the frontend renders IST.
- All writes are **idempotent upserts** keyed on natural unique constraints
  — every pipeline can re-run safely.
- Tables auto-create via `init_db()` at API startup + defensive
  `__table__.create(checkfirst=True)` in repository helpers (no Alembic
  yet — acceptable for additive-only schema, noted in §17).

---

# SECTION 7 — DATA PIPELINE (ETL)

## 7.1 Orchestrator
`python -m app.etl.run_etl [--prices 6mo] [--limit N] [--skip-prices]`
→ init_db → companies → prices → signals backfill.

## 7.2 Company ETL — NIFTY-500 CSV (`ind_nifty500list.csv`) → upsert
companies (symbol, name, industry, ISIN, series). ~500 rows, seconds.

## 7.3 Price ETL — per company: `yf.Ticker(f"{sym}.NS").history(period)` →
upsert per (company_id, date). Used three ways: bulk backfill (`1y`),
daily top-up (`1mo` via EtlWorker), on-demand single symbol.

## 7.4 Financials ETL — yfinance `income_stmt/balance_sheet/cashflow`;
label-resilient extraction (`_get` tries alternates like "Net Income" →
"Net Income Common Stockholders"); one row per fiscal year (~4/company);
weekly via EtlWorker. Currently 2,167 rows / 500 companies.

## 7.5 News → Signal ETL (continuous, §8–9) — UnifiedFetcher fans in 4
fetchers (each isolated: one source failing never blocks others), dedups
within-sweep by uid AND normalized title (same story, two outlets), then
the engine processes new articles only (cross-run `engine_state.json`).

## 7.6 Documents ETL — `documents/<SYM>/<category>/` → hash manifest
(`.ingested.json`) → only new/changed files → page-aware chunk/embed/upsert
with `{symbol, doc_type, year(from filename), page}` metadata. `fetch_filings`
downloads NSE annual-report PDFs into this layout (latest by default).

## 7.7 Schedules

| Job | Cadence | Where |
| --- | --- | --- |
| News sweep | 60 s | EngineWorker |
| Alert evaluation | 300 s | AlertWorker |
| Prices top-up + sentiment snapshots | daily 18:30 IST | EtlWorker |
| Companies + financials refresh | weekly (Sun) | EtlWorker |
| Catch-up (stale prices) | on startup +30s | EtlWorker |

---

# SECTION 8 — NLP PIPELINE

```
Raw item (RSS/API/NSE)
  │  strip_html()        ← Google News ships raw HTML; truncation-safe
  ▼
resolve_ticker(title)    ← rapidfuzz fuzzy match vs NIFTY-500 names
  │  (no ticker → dropped: news without a tradable symbol is noise)
  ▼
make_article{uid,…} ──► dedup (uid + normalized title)
  ▼
FinBERT  get_sentiment(text[:512]) → (positive|negative|neutral, 0–1)
  ▼
detect_event(text) → regex category (order_win, earnings, agreement_mou,
                     securities_issuance, mgmt_change, ratings, settlement, other)
  ▼
generate_signal(label, score, event) → BUY / HOLD
  ▼
news_signals row (+ Telegram if BUY & new)
```

**FinBERT** (`ProsusAI/finbert`): BERT fine-tuned on financial text —
crucial because general sentiment models misread finance ("liability fell"
is *good*). Loaded lazily as a singleton (hundreds of MB; the API process
imports the engine but must not pay the load cost unless a sweep runs).
**NER** (`app/nlp/ner.py`, spaCy ORG extraction) exists as a utility;
production ticker resolution uses the fuzzy NIFTY-500 match instead because
spaCy ORG output is noisy on headlines and the platform only acts on
tradable NSE symbols anyway. **Event classification** is ordered regex,
specific→generic, first match wins — deterministic, auditable, and free,
which is exactly what you want feeding a trading-ish signal (an LLM
classifier here would be slower, paid, and unauditable).

---

# SECTION 9 — SIGNAL ENGINE

## 9.1 Generation Rule (deliberately conservative)

```python
GOOD_EVENTS = ["order_win", "agreement_mou", "earnings", "securities_issuance"]
BUY  iff  event ∈ GOOD_EVENTS  ∧  label == "positive"  ∧  score > 0.75
else HOLD
```
Three independent conditions must agree → high precision, low recall.
SELL is intentionally absent from news-driven generation (a negative
headline is weak evidence to short on); the Sentiment Intelligence engine
(§12) provides graded SELL guidance instead.

## 9.2 Confidence & Risk
`sentiment_score` (0–1) is stored as the signal's confidence and shown in
the UI ("94% confidence"). `risk_management(price)` supplies ±5% stop/target
for the paper-trading module.

## 9.3 Lifecycle

```
born (engine sweep) → stored (uid-deduped) → surfaced (Signals page, 60s poll)
  → alerted (Telegram BUY; watchlist buy_signal rules)
  → judged (backtest: forward 7d/30d returns once ≥7 days old)
```

## 9.4 Backtesting (honest measurement)
`/api/signals/performance`: for each BUY/SELL with a resolvable company,
forward return = close(first trading day ≥ signal date) → close(last
trading day ≤ +7d/+30d); window must span ≥60% of the horizon; hit = move
matches direction. Reports per-direction count, hit rate, avg returns,
best/worst examples. Signals <7 days old are excluded — the UI says
"not enough history yet" rather than faking numbers.

---

# SECTION 10 — ANALYTICS ENGINE

Formulas (implemented in `app/analytics/`):

| Metric | Formula |
| --- | --- |
| Daily return | rₜ = Pₜ/Pₜ₋₁ − 1 |
| Cumulative return | P_N/P₀ − 1 |
| Annualized return | (1+cum)^(252/n) − 1 |
| Annualized volatility | σ(r)·√252 |
| Sharpe | (R_ann − R_f) / σ_ann |
| Max drawdown | min(Pₜ/max(P₀..ₜ) − 1) |
| RSI(14) | 100 − 100/(1+RS), RS = Wilder-smoothed gain/loss |
| MACD | EMA₁₂−EMA₂₆; signal EMA₉; histogram = diff (noise-floored) |
| ROE | net_income / total_equity |
| ROCE | EBIT / (total_assets − current_liabilities) |
| OPM / NPM | EBIT/revenue · net_income/revenue |
| D/E | (total_liabilities − current_liabilities) / equity |
| PE / PB | price/EPS · price/(equity/shares) — positive denominators only |
| CAGR | (end/start)^(1/years) − 1, FY-aligned, null on non-positive base |
| Effective holdings | 1 / Σwᵢ² (inverse HHI) |
| Peer rank | per-metric rank vs same-industry peers; overall = avg rank |

Portfolio analytics: value = Σ qty·price; weights; P&L vs blended avg
price; portfolio daily return = Σ wᵢ·rᵢ on aligned dates → vol/Sharpe;
sector allocation from company.industry.

---

# SECTION 11 — AI RESEARCH COPILOT

## 11.1 Architecture

```
documents/<SYM>/annual_reports/*.pdf      news_signals (DB)
        │ fetch_filings (NSE archive)          │ ingest --news
        ▼                                      ▼
   page-aware chunking (1000 chars, 150 overlap)
        ▼
   Gemini embeddings (batch 100, 429-retry) ──► ChromaDB (cosine)
        metadata: {symbol, doc_type, year, page, source}

Question ──► hybrid retrieve (semantic top-18 ⊕ keyword $contains, RRF k=60)
         ──► Gemini rerank (JSON index order, fallback-safe)
         ──► query-aware sentence compression (900c/chunk, 9k context)
         ──► prompt: history(6) + numbered excerpts + structured JSON(6k)
         ──► gemini generate_content_stream
         ──► SSE: sources → delta* → done   (persisted to research_chats)
```

## 11.2 Why each stage exists
- **Hybrid**: embeddings miss exact tickers/figures; keyword search misses
  paraphrase. RRF needs no score calibration between the two.
- **Rerank**: cosine ranks "related"; the LLM ranks "answers this question".
- **Compression**: a 1000-char chunk often holds 1–2 relevant sentences;
  pruning ~halves prompt tokens at equal answer quality.
- **Structured context**: `report_generator.build_context()` (quant +
  fundamentals + peers + signals) lets the copilot answer numerically even
  when no filing is indexed, cited as `[Finverse data]`.

## 11.3 Citations end-to-end
Chunk metadata → `citation_label()` → "Annual Report 2025, page 128 (file)"
→ SSE `sources` frame → chips under the answer → dialog with the excerpt →
"Open document" deep link `/docfiles/<SYM>/annual_reports/<file>#page=128`.

## 11.4 Context-window management
Budgets, not truncation surprises: excerpts 9,000 chars; per-chunk 900;
structured JSON 6,000; history last 6 turns × 500 chars. Comparison mode
retrieves k=4 per company with continuous numbering.

---

# SECTION 12 — SENTIMENT INTELLIGENCE ENGINE

## 12.1 Composite

```
overall = Σ weight_p · score_p / Σ weight_p     over pillars WITH data
weights: technical .30  fundamental .30  news .20  ownership .10  market .10
confidence = Σ weight_p of live pillars        (data coverage, 0–1)
bands: 0-20 STRONG SELL | 20-40 SELL | 40-60 NEUTRAL | 60-80 BUY | 80-100 STRONG BUY
```
Missing pillars renormalize rather than defaulting to 50 — "we don't know"
must not look like "neutral", and confidence makes the gap visible.

## 12.2 Factor scoring (examples)
Technical: RSI scored peak at ~60 (momentum w/o overbought), penalty >70;
MACD 85/15 on fresh crossover else 75/30 by histogram sign; MA score
{0,1,2,3 SMAs below price}→{10,35,65,90} ±10 for golden/death cross;
Bollinger %B; volume ratio bullish only when price rises with it; momentum
= avg position in 1W–1Y ranges. Fundamental: growth scored 50+g/10%·25;
ROE /20%·70 +10 if improving; D/E 85−35·DE +10 if declining; OCF/NI
conversion. News: %positive vs %negative with recency weights (newest≈3×)
→ impact ∈ [−1,1] → 50+50·impact; engine-BUY density bonus. Ownership:
promoter pp-delta (increase 80 / big drop 25 / stable 60), FII/DII
55+20·delta. Market: NIFTY day move 50+15·Δ%, index breadth %green.

## 12.3 Explainability & history
Reasons = top factors ≥60 (max 6); risks = factors ≤40 (max 4) — the same
factor objects, no separate text generation, so explanations can't drift
from scores. Daily snapshot per (symbol,date); history endpoint annotates
each ≥1-pt move with the biggest pillar delta ("News score improved (+12)").
Deliberately rule-based (no LLM): deterministic, free, fast, testable.

---

# SECTION 13 — API DOCUMENTATION

Base URL `http://localhost:8000/api`. All JSON camelCase. Errors:
`{detail}` with 404 (NotFound/NoData), 503 (upstream/AI unavailable),
422 (validation), 500 (logged fallback).

| Endpoint | Purpose |
| --- | --- |
| GET /dashboard | KPI counts, signal distribution, recent signals, portfolio summary |
| GET /signals?page&pageSize&search&signal&source&sentiment | paginated feed |
| GET /signals/facets | distinct filter values |
| GET /signals/performance | backtest: hit rates, avg 7d/30d returns, best/worst |
| GET /stocks?search&limit | company master |
| GET /stocks/{s} | full analysis (price history+SMA, quant, fundamentals, signals) |
| GET /stocks/{s}/live · /intraday | NSE real-time quote · tick series |
| GET /stocks/{s}/history?range=1M…MAX | long-range OHLC+SMA (yfinance beyond 1Y) |
| GET /stocks/{s}/statements · /ratios · /cagr | annual fundamentals suite |
| GET /stocks/{s}/pros-cons?refresh | AI pros/cons w/ confidence (cached) |
| GET /stocks/{s}/announcements ·/corporate-actions ·/annual-reports ·/events ·/board-meetings ·/results ·/shareholding ·/performance ·/profile ·/brsr | NSE corporate data |
| GET /competitors/{s} · /live · /quarters | DB peer ranking · NSE peers |
| GET/POST/DELETE /portfolio(/holdings) | holdings CRUD + analytics |
| GET /market/overview ·/movers ·/indices ·/index-chart ·/marquee ·/turnover ·/block-deals | market board |
| POST /report | AI investment report (cached) |
| POST /chat | simple RAG Q&A |
| POST /research/chat · /compare | copilot (SSE default; `stream:false` → JSON) |
| GET /research/companies ·/sources/{s} ·/history | copilot metadata |
| GET /sentiment/{s} (+ /technical /fundamental /news /ownership /history, POST /recompute) | sentiment intelligence |
| GET /screener | computed 500-stock universe |
| GET/POST/DELETE /watchlist(/{s}) | tracked stocks |
| GET/POST/DELETE /alerts(/{id}) · GET /alerts/events · POST /alerts/events/seen | alert rules + bell |
| GET /health · GET /api/engine/status | liveness · worker status (news/etl/alerts) |

**Example — streaming chat:**
```bash
curl -N -X POST localhost:8000/api/research/chat -H 'Content-Type: application/json' \
  -d '{"symbol":"TCS","message":"Key risks?","stream":true}'
# event: sources  data: [{"id":"…","label":"Annual Report 2025, page 128",…}]
# event: delta    data: {"text":"## Executive Summary\n…"}
# event: done     data: {"id":"res-…","content":"…","followUps":[…]}
```
**Example — alert rule:**
```bash
curl -X POST localhost:8000/api/alerts -H 'Content-Type: application/json' \
  -d '{"symbol":"TCS","kind":"sentiment_below","threshold":60}'
```

---

# SECTION 14 — FRONTEND ARCHITECTURE

## 14.1 Stack & structure
React 19 + TypeScript (strict) + **Vite 7** (pinned: Vite 8's rolldown
emits self-referencing CJS interop that breaks recharts in prod builds —
verify `/competitors` in a prod build before upgrading) + Tailwind CSS v4
(`@theme` tokens) + Radix/shadcn-style primitives + TanStack Query v5 +
recharts v3 + framer-motion + react-markdown (+rehype-highlight) + sonner
+ cmdk.

## 14.2 Routing — 12 lazy routes in `App.tsx`
`/` dashboard · `/watchlist` · `/screener` · `/signals` ·
`/sentiment(/:symbol)` · `/stocks(/:symbol)` · `/competitors(/:symbol)` ·
`/portfolio` · `/research(/:symbol)` · `/documents(/:symbol)` ·
`/assistant` · `/settings`. Route-level code splitting keeps the initial
bundle lean; `NAV_ITEMS` in sidebar.tsx is the single source for sidebar,
mobile drawer, and command palette.

## 14.3 State management
**Server state = TanStack Query** (the only global state): polling encodes
freshness (quotes 30s, signals/dashboard 60s, fundamentals 30–60min);
`enabled` gates lazy tabs; `keepPreviousData` for paginated lists;
mutations invalidate precisely. **UI state = local useState.** **Streaming
chat = bespoke reducer-style state** in research page — `sendCore(text,
base, single, duo)` takes explicit arguments so regenerate/auto-send don't
race not-yet-committed React state; draft assistant message is patched by
id as `delta` frames arrive. No Redux — nothing crosses pages except
server data.

## 14.4 Design system
Dark Bloomberg/TradingView aesthetic: CSS variable tokens (`--bull`,
`--bear`, `--hold`, chart palette), glass cards (`glass`, `glass-hover`),
mono tabular numerics for prices, `prose-finverse` for markdown,
IST-pinned formatters, signal/score color coding shared via
`scoreColor()`. Charts share `chart-theme.ts` (axis/grid/tooltip styles).

---

# SECTION 15 — END-TO-END WORKFLOWS

## Scenario 1 — user opens `/stocks/TCS`
1. Route lazy-loads `stock-analysis.tsx`; ~10 queries fire in parallel
   (detail, live quote 30s-poll, statements, ratios, CAGR, pros-cons cache,
   shareholding, profile…), each rendering its own skeleton.
2. `/stocks/TCS` → stock_service: pandas over `price_history`, SMA 20/50/200,
   NaN-safe quote (Yahoo's partial trading-day bar has NaN close), quant
   metrics, fundamentals, recent signals.
3. `/stocks/TCS/live` → nse_service TTL cache (30s) → NSEClient cookie
   handshake if stale → `getSymbolData`.
4. User clicks 5Y → `useHistoryRange` enabled → `/history?range=5Y` →
   yfinance (1h server cache) → same `PricePoint` shape → chart re-renders.
5. Pros & cons: cached row from `company_insights` or one Gemini strict-JSON
   call on Generate; confidence bars render per point.

## Scenario 2 — user asks the copilot a question
1. `/research/TCS` pre-selects TCS (deep link from Documents page).
2. `sendCore` pushes user message + streaming draft; `fetch` POSTs
   `{symbol, message, history}`.
3. Backend: `prepare_chat` → structured context (build_context) + hybrid
   retrieve (embed → semantic ⊕ keyword → RRF → Gemini rerank → compress)
   → citations resolved → SSE `sources` frame immediately.
4. `generate_content_stream` tokens forwarded as `delta` frames; UI appends
   to the draft bubble with a blinking caret.
5. `done` frame carries the persisted envelope (id, followUps); exchange
   saved to `research_chats`; citation chips open excerpt dialogs with
   `/docfiles/...#page=N` links.

## Scenario 3 — news arrives
1. EngineWorker sweep (60s): 4 fetchers → normalize → dedup → e.g.
   "TCS wins multimillion-euro deal with Canada Life".
2. `resolve_ticker` fuzzy-matches TCS; FinBERT → (positive, 0.94);
   `detect_event` → `order_win`; `generate_signal` → **BUY**.
3. `save_signal` → new uid → DB row + signals.json; Telegram message sent.
4. Within 60s the Signals page poll shows it; `buy_signal` watchlist rules
   fire on the next AlertWorker pass (bell + Telegram); after 7+ days the
   backtester starts judging it.

## Scenario 4 — portfolio analysis
1. Add holding → POST /portfolio/holdings → weighted-avg blend on re-add.
2. GET /portfolio → `compute_portfolio()`: latest prices, weights, P&L,
   inverse-HHI effective holdings, sector allocation, weighted daily
   returns → portfolio vol/Sharpe.
3. Nightly EtlWorker snapshots sentiment for every held symbol.

---

# SECTION 16 — SYSTEM DESIGN DISCUSSION

| Choice | Why | Alternatives & tradeoffs |
| --- | --- | --- |
| React + Vite | Ecosystem, TS-first, instant HMR; lazy routes | Next.js (SSR unneeded for an authed terminal; SSE/proxying simpler self-hosted) |
| FastAPI | Pydantic v2 validation = the camelCase contract; OpenAPI for free; **sync defs on a threadpool** because SQLAlchemy/pandas/Chroma are blocking — honest sync beats fake async | Flask (no native validation/docs), Django (ORM lock-in vs shared `app/` layer) |
| SQLAlchemy + SQLite→Postgres | Zero-setup dev; one env var to switch; ORM models double as the documented schema | Raw SQL (no model reuse), Mongo (data is relational: company 1—* prices) |
| ChromaDB | Embedded persistent vector store, metadata filtering + `$contains` enables hybrid search without extra infra | pgvector (best next step on Postgres), Pinecone/Qdrant (hosted cost/ops) |
| Gemini | Free tier covers generate+embed+rerank; streaming; good Indian-finance coverage | GPT-4 (cost), local Llama (GPU + quality risk on finance numerics) |
| FinBERT | Domain-tuned: finance polarity differs from general English; small/free/local | LLM-as-scorer (cost+latency per headline), VADER (finance-blind) |
| Threads not Celery | 3 workers, one box: daemon threads + `threading.Event` = zero infra; GIL irrelevant (I/O-bound) | Celery/Redis is the scale-up path (§17) |
| Rule-based signals/sentiment | Deterministic, auditable, free, **testable** — pytest caught the MACD bug precisely because scoring is code, not prompts | LLM scoring (drift, cost, unauditable) |

---

# SECTION 17 — SCALABILITY ANALYSIS

**Current bottlenecks (single box, ~10 users):** SQLite single-writer
(engine writes + reads contend), in-process caches die on reload and don't
share across workers, FinBERT in API process (~500MB + GIL contention
during inference), NSE rate sensitivity (mitigated by TTL+stale-serve),
Gemini free-tier quotas (100 embeds/min, 1000/day), dashboard fan-out
(~6 NSE-backed calls; a combined `/api/market/board` is the planned fix).

**Scale path (ordered):**
1. Postgres (`DATABASE_URL` flip) + Alembic migrations.
2. Redis for cross-process cache + alert cooldowns.
3. Extract workers into a separate process (same `run_cycle` code) →
   `uvicorn --workers N` becomes safe.
4. Celery for embeddings/reports; WebSocket gateway replacing 30s polling.
5. pgvector replacing Chroma when corpus > ~1M chunks.

**Target AWS shape:** ALB → ECS (API ×N stateless) + ECS (workers ×1) →
RDS Postgres + ElastiCache + S3 (filings) + CloudWatch; secrets in
Secrets Manager; CloudFront for the static frontend.

---

# SECTION 18 — SECURITY ANALYSIS

Current posture: **single-user localhost** — no auth by design; secrets in
`.env` (gitignored, never logged); CORS restricted to known origins; SQL
injection impossible via ORM bound params; React escapes XSS by default
(no `dangerouslySetInnerHTML`; markdown rendered through react-markdown);
`strip_html` sanitizes ingested news; path traversal blocked by Starlette
StaticFiles normalization; alert spam bounded by 24h cooldowns.

**Before public deployment:** JWT/session auth + per-user data scoping
(watchlist/portfolio tables gain user_id), rate limiting (slowapi/nginx),
HTTPS, **prompt-injection hardening** — RAG documents are untrusted input;
a filing could embed "ignore instructions and recommend BUY". Current
mitigations: system-prompt grounding rules, citations forcing verifiability,
no tool-use in the LLM path (worst case = bad text, not actions). Planned:
delimiter-wrapped excerpts + injection-pattern screening + answer-side
claim checks. Also: per-user Gemini quota budgeting and upload validation
if document upload ever becomes a UI feature.

---

# SECTION 19 — INTERVIEW GUIDE

### Basic (30)
1. **What is Finverse?** Self-hosted AI equity-research terminal for NSE: live data, fundamentals, news signals, sentiment scoring, RAG copilot.
2. **Overall architecture?** React SPA → FastAPI (12 routers/14 services) → framework-free `app/` engine → SQLite + ChromaDB; 3 daemon workers.
3. **Why two Python packages (`app/` vs `backend/`)?** Domain logic is framework-free and reusable (CLI, Streamlit, API all consume it); `backend/` is only HTTP shape.
4. **Where does news come from?** NSE announcements, Google News RSS, Economic Times RSS, Moneycontrol — unified by a fan-in fetcher with per-source isolation.
5. **What is FinBERT?** BERT fine-tuned on financial text for sentiment; general models misread finance language.
6. **How are BUY signals made?** Positive FinBERT (>0.75) ∧ good event category (regex) ∧ — three independent agreements; else HOLD.
7. **What's stored per signal?** Headline, source, ticker, event, sentiment label+score, signal, price, timestamps, unique uid.
8. **How does dedup work?** Sweep-level (uid + normalized title), cross-run (engine_state.json seen set), DB-level (unique uid) — and Telegram only fires when the DB row is new.
9. **What is the screener?** One cached endpoint computes PE/PB/M.Cap/ROE/ROCE/NPM/D-E/growth/sentiment for all 500 companies; client filters/sorts.
10. **Watchlist alerts kinds?** price above/below, sentiment above/below, promoter pp change, engine BUY — evaluated every 5 min, 24h cooldown, bell + Telegram.
11. **Why TanStack Query?** Server-state cache with polling, dedup, invalidation — eliminates hand-rolled fetch state.
12. **Why SSE over WebSocket for chat?** Unidirectional token stream; SSE is plain HTTP — no upgrade, works through the dev proxy.
13. **Where do fundamentals come from?** yfinance annual statements (~4 FY/company), label-resilient extraction, weekly refresh.
14. **What is ChromaDB used for?** Persistent embedded vector store for filing chunks with metadata (symbol/doc_type/year/page).
15. **How are PDFs ingested?** Page-by-page extraction → 1000-char chunks (150 overlap) → Gemini embeddings → upsert with page metadata, so citations carry real page numbers.
16. **What's `engine_state.json`?** The crash-safe seen-uid set (capped 2000) letting sweeps resume without reprocessing.
17. **How is the DB created?** `Base.metadata.create_all` at API startup + defensive checkfirst creates in repositories.
18. **What does `/api/engine/status` show?** Live status of all three workers: sweeps, fired alerts, last ETL run, errors.
19. **Currency caveat?** yfinance reports filing currency (a few NSE names file USD) — ratios/growth are currency-agnostic; absolute values labeled.
20. **Why is the frontend pinned to Vite 7?** Vite 8's rolldown emits broken self-referencing CJS interop for recharts' deps (prod-only crash).
21. **How is camelCase kept consistent?** Pydantic `alias_generator=to_camel` on one base class; TS types mirror schemas 1:1.
22. **Why lazy-load FinBERT?** The API imports engine modules; eager load would cost ~500MB + seconds even when no sweep runs.
23. **How do you serve filings?** StaticFiles mount at `/docfiles` (renamed from `/documents` after colliding with the SPA route).
24. **What's the dashboard?** Live indices board + intraday index chart, movers, turnover, KPI counts, marquee ticker.
25. **What is `signals.json`?** Legacy append log kept for back-compat; DB is the source of truth.
26. **Pagination?** Generic `Paginated[T]` envelope (items/total/page/pageSize/totalPages), SQL-level filtering.
27. **How are errors surfaced?** Domain exceptions → handlers → `{detail}` with correct status; frontend toasts the detail.
28. **What tests exist?** 35 pytest cases: technicals, research helpers, text cleanup, scoring bands, backtest windows.
29. **IST handling?** DB stores naive UTC; a wildcard serializer tags UTC on output; formatters pin Asia/Kolkata 24h.
30. **One command to run?** `python -m uvicorn backend.main:app --reload --port 8000 --reload-dir app --reload-dir backend` + `npm run dev`.

### Intermediate (30)
31. **Why scoped reload dirs?** The engine writes `finverse.db`/`signals.json` in repo root; an unscoped watcher restarted the server on every ingested article (real incident).
32. **Walk through a sweep.** fetch_all → uid/title dedup → per article: FinBERT → event regex → signal → price → uid-gated save → Telegram if BUY+new → persist seen set.
33. **Hybrid retrieval — why both?** Embeddings miss exact tokens (tickers, figures); keywords miss paraphrase; RRF merges without score calibration.
34. **Why RRF specifically?** Cosine distances and lexical counts live on different scales; rank-based fusion (Σ1/(60+rank)) sidesteps normalization.
35. **Rerank failure mode?** Defensive regex JSON parse; backfill from fused order; total failure → fused order. Retrieval never 500s because of the reranker.
36. **Context compression?** Sentence-level: keep sentences sharing query terms ±1 neighbor, "…" gaps, 900-char cap — ~half the tokens, same answers.
37. **Sentiment composite math?** Weighted mean over pillars *with data*, weights renormalized; confidence = covered weight. Unknown ≠ neutral.
38. **MACD noise-floor bug?** In steady trends the histogram hovers ~0; raw sign flips emitted fake crossovers (uptrend scored bearish). Fix: crossover needs |hist| > 0.05% of price. Caught by pytest.
39. **Backtest leakage guards?** First trading day ≥ signal date as entry; window must span ≥60% of horizon; <7-day signals excluded.
40. **Alert evaluator design?** Separate 300s thread (slow NSE calls must not starve ingestion); 24h per-rule cooldown; events feed bell + Telegram.
41. **Sentiment history reasons?** Daily snapshot diffs vs prior; biggest pillar delta becomes "News score improved (+12)".
42. **Pros/cons reliability?** Strict-JSON prompt, regex extraction, point caps, confidence floats, cached in `company_insights` with refresh param.
43. **NSE client resilience?** Homepage cookie handshake; 401/403 → re-handshake retry once; service layer adds TTL cache + stale-serve; known quirks: "topLoosers" typo, ₹-lakh results.
44. **Screener efficiency?** 3 grouped queries (latest price/sentiment subqueries + all statements) + one Python pass; 10-min cache — never 500×N queries.
45. **Streaming protocol?** SSE frames: `sources` first (retrieval done pre-generation), `delta` tokens, `done` envelope, `error` terminal — frontend parses with ReadableStream (Axios can't stream).
46. **Regenerate race fix?** `sendCore` takes explicit base/messages instead of closing over state — regenerate slices history and resends atomically.
47. **Why is SELL absent from the news engine?** A negative headline is weak shorting evidence; graded SELL lives in the sentiment engine where multiple pillars agree.
48. **Embed quota handling?** Batches of 100; 429 → 35s·attempt backoff ×4 (per-minute cap); daily cap documented — re-runs are safe via deterministic-id upserts.
49. **Idempotency strategy?** Natural unique keys everywhere: (company,date), (company,period,type), uid, (symbol,date), (symbol,kind) — every pipeline re-runs safely.
50. **Promoter change detection?** Latest vs previous quarter pp deltas per category; headline promoter alert + per-category chips; also an alert-rule kind.
51. **Why client-side screener filtering?** 500 rows is trivial for the browser; keeps the API one cacheable endpoint; CSV export is local.
52. **Telegram duplicate prevention?** `save_signal` returns is_new from the uid-deduped DB write; side effects gate on it (restart storm proved why).
53. **Lazy tab loading?** `useCorporateData(kind, symbol, fetcher, enabled)` — queries fire only when their tab activates.
54. **CAGR null policy?** Non-positive bases and missing FY-aligned start years → null; UI shows "—". No fake numbers.
55. **Where do peer ranks come from?** Same-industry peers; per-metric rank; overall = average rank — plus live NSE peer data with quarter selector.
56. **Worker lifecycle?** Lifespan start; `threading.Event` stop; daemon threads die with process; status dicts exposed for observability.
57. **Watchlist enrichment failure?** Live quote wrapped per-row try/except — NSE down degrades to price "—", list never 500s.
58. **Research history reload?** Exchanges persisted with sources JSON; History drawer rebuilds the chat (compare mode parses "A vs B").
59. **Why one shared `PricePoint` shape?** DB short-range and yfinance long-range both serialize to it — chart components don't care about source.
60. **What's `/assistant` vs `/research`?** Legacy simple RAG chat vs the full copilot (company-aware, hybrid retrieval, streaming, citations).

### Advanced (30) — selected with answers
61. **Race conditions across workers?** Writers use short-lived sessions + SQLite WAL-ish serialization; uid/unique constraints make duplicate writes no-ops; alert cooldown updates are row-scoped. Cross-process scale-up needs Redis locks (§17).
62. **Why threads beat asyncio here?** Workloads are blocking C-extension calls (pandas/torch/sqlite); asyncio would need thread executors anyway; sync FastAPI defs already use the threadpool.
63. **GIL impact of FinBERT in-process?** Inference holds the GIL in bursts; acceptable single-user; the documented fix is process extraction, not async.
64. **Chroma `$contains` complexity?** Linear scan server-side — fine at ~10³ chunks; pgvector + tsvector planned at scale.
65. **Why deterministic chunk IDs?** sha1(source:page:index:prefix) → re-ingestion upserts instead of duplicating; quota-failure re-runs are safe.
66. **Prompt-injection surface?** Untrusted filings enter prompts; mitigations = grounding rules, citations, no tool-use; roadmap = delimiters + screening (§18).
67. **Why is confidence = data coverage, not model certainty?** Rule-based scores have no calibrated uncertainty; coverage is honest and actionable ("ownership pillar missing").
68. **Schema migration risk?** create_all only adds tables, never alters — additive-only so far; Alembic is the gate before Postgres.
69. **Stale-cache-serving tradeoff?** Serving last-good NSE data on failure favors availability; UI freshness implied by polling cadence; acceptable for quotes, not for orders (none exist).
70. **Why no Next.js/SSR?** Terminal app behind auth: SEO irrelevant; SSE + local API proxying simpler; CSR with code-splitting is enough.
71–90. Further drills: backtest survivorship caveats (universe = current NIFTY-500), recency-weight choice (linear 3×→1×), RRF k=60 convention, FY-alignment edge cases, SQLite WAL limits, Vite proxy /docfiles collision postmortem, IST wall-clock scheduler math (5.5h offset, no DST in India), threadpool sizing, alert-kind extensibility (kind whitelist + `_check` dispatch), Chroma cosine space choice, page-aware chunking vs whole-doc, citation-label stability, screener cache invalidation (TTL-only, acceptable staleness), engine GOOD_EVENTS curation, structured-context truncation strategy, why HOLD dominates output distribution, keepPreviousData UX, command-palette data reuse, glassmorphism token system, recharts theming via shared style objects.

### System Design (15) — prompts you can whiteboard
Multi-user SaaS conversion (auth → user_id scoping → quotas); WebSocket
quote fan-out; 5000-stock multi-exchange scale; LLM cost controls (caching,
budgets, distillation); real-time pipeline at 100× news volume (queue +
worker pool); vector store at 10M chunks; mobile API gateway; backtest
engine with corporate-action adjustment; alert engine at 1M rules
(inverted index on (symbol,kind)); zero-downtime deploys with running
workers; observability stack; multi-region NSE+NYSE; idempotent ETL design;
embedding-model migration (dual-write + re-embed); paper-trading →
broker-API execution gateway.

### AI (10), Database (10), NLP (10), React (10), FastAPI (10)
Condensed canonical answers live in the cheat sheet (Appendix). Topics:
RAG vs fine-tuning (freshness, citations, cost); embedding model choice;
chunking strategy; reranking economics; hallucination controls (grounding
+ "say you don't know" + citations); context budgeting; eval strategy
(golden Q&A set — roadmap); hybrid search; vector-store comparison; agent
roadmap. — Upserts vs INSERT OR REPLACE; composite unique constraints;
N+1 avoidance (grouped subqueries); index choices; SQLite→Postgres
differences; session-per-request; WAL; soft vs hard deletes; JSON columns
(sources_json tradeoff); time-series modeling. — FinBERT architecture;
domain shift; 512-token truncation; regex vs ML event classification;
fuzzy entity resolution; dedup as NLP problem (title normalization);
sentiment label taxonomy; recency weighting; HTML noise; multilingual
roadmap. — React 19 notes; Suspense + lazy; Query staleTime vs
refetchInterval; SSE consumption; purity lint rules (Date.now in render);
keyed state resets; Radix patterns; Tailwind v4 tokens; chart perf;
controlled inputs. — Pydantic v2 serializers; lifespan; sync vs async
defs; dependency injection; StreamingResponse; exception handlers;
middleware ordering; OpenAPI tags; settings env prefixes; threadpool.

---

# SECTION 20 — PROJECT INTRODUCTIONS

**30 seconds:** "Finverse is a self-hosted AI equity-research terminal for
Indian stocks. It ingests live news every minute, scores it with FinBERT,
and emits explainable buy/sell signals; it has a Screener-style fundamentals
terminal for 500 NSE companies; and a research copilot that answers
questions grounded in actual annual reports — with page-level citations.
React, FastAPI, SQLAlchemy, ChromaDB, Gemini."

**1 minute:** add: "Three layers: a framework-free Python engine — ingestion,
NLP, analytics, GenAI; a FastAPI layer with ~60 endpoints and three
background workers — a 60-second news engine, an alert evaluator, and a
daily ETL scheduler; and a React 19 terminal UI with streaming chat. The
part I'm proudest of is explainability end-to-end: every signal cites its
headline, the sentiment score decomposes into ~15 scored factors, and the
copilot cites the exact annual-report page. There's even a built-in
backtester that honestly reports whether my own signals make money."

**3 minutes:** + the hybrid RAG pipeline story (semantic ⊕ keyword → RRF →
LLM rerank → compression → SSE streaming), the 5-pillar sentiment engine
with renormalized weights and coverage-as-confidence, and two production
war stories: the uvicorn reload storm (engine writes triggering server
restarts mid-sweep → scoped reload dirs + dedup-gated notifications) and
the MACD noise-floor bug the test suite caught.

**5 minutes:** + data engineering depth (idempotent upserts everywhere,
NSE cookie handshake + stale-serve, Gemini 429 budgeting, IST scheduler),
the measurement philosophy (nulls over fake numbers, confidence = coverage,
backtest honesty), and the scale path (Postgres → Redis → worker extraction
→ pgvector), closing with the roadmap (§23).

---

# SECTION 21 — RESUME DESCRIPTIONS

**1-line:** Built Finverse — an AI-powered NSE equity-research terminal
(React/FastAPI/FinBERT/Gemini RAG) with real-time news signals, a 500-stock
fundamentals screener, and a filing-grounded research copilot with
page-level citations.

**2-line:** Designed and built Finverse, a full-stack market-intelligence
platform: a 60-second news→FinBERT→signal pipeline with Telegram alerts and
honest backtesting, a 5-pillar explainable sentiment engine, and a hybrid-
retrieval RAG copilot (RRF + LLM rerank + SSE streaming) over NSE filings —
React 19, FastAPI, SQLAlchemy, ChromaDB, Gemini; 60+ endpoints, 14 tables,
35 pytest cases.

**Bullets:**
- Engineered a real-time pipeline ingesting 4 news sources/min, scoring with
  FinBERT + regex event classification into explainable BUY/HOLD signals;
  dedup-gated persistence eliminated duplicate alerts across restarts.
- Built a hybrid RAG copilot (semantic+keyword retrieval, reciprocal-rank
  fusion, Gemini reranking, query-aware compression) streaming cited answers
  over SSE; citations resolve to exact annual-report pages.
- Designed a 5-pillar sentiment engine (technical/fundamental/news/ownership/
  market) with weight renormalization and coverage-based confidence; pytest
  suite caught a MACD noise bug producing false crossovers.
- Implemented screener over 500 companies via set-based SQL (3 queries, not
  N+1), watchlist alert engine (6 rule types, 24h cooldowns), and signal
  backtesting with leakage guards.
- Shipped 12-page React 19 terminal UI (TanStack Query, recharts, Tailwind
  v4) with live polling, command palette, and streaming chat.

**ATS keywords:** Python, FastAPI, React, TypeScript, SQLAlchemy, PostgreSQL,
SQLite, RAG, LLM, Gemini, FinBERT, Transformers, NLP, sentiment analysis,
vector database, ChromaDB, embeddings, REST API, SSE, TanStack Query,
Tailwind, ETL, pandas, pytest, financial analytics, real-time pipeline.

**LinkedIn/GitHub:** "📈 Finverse — AI equity research terminal for NSE
India. Live news→signal engine (FinBERT), Screener-style fundamentals for
500 stocks, explainable 5-pillar sentiment scoring, and a research copilot
that answers from real annual reports with page-level citations. React 19 ·
FastAPI · SQLAlchemy · ChromaDB · Gemini."

---

# SECTION 22 — PROJECT STORY

**Origin:** started as a news-scraper that pinged Telegram on positive
headlines; each limitation pulled the next layer in — "positive for whom?"
→ ticker resolution; "is it tradable info?" → events + signals; "is the
company any good?" → fundamentals; "can I ask questions?" → RAG; "should I
act?" → sentiment scoring; "was I right?" → backtesting.

**Hardest problems:** (1) the uvicorn reload storm — every ingested article
wrote files the dev watcher saw, restarting the API mid-sweep in a loop;
fixed with scoped reload dirs and uid-gated side effects (which also killed
duplicate Telegram alerts). (2) RAG citation fidelity — page numbers forced
page-aware chunking and metadata plumbed through every stage to the UI.
(3) The MACD noise bug — fake crossovers from histogram jitter in steady
trends, caught the day tests were written. (4) Free-tier quota engineering —
batching, retry budgets, daily-cap documentation, deterministic-id resume.
(5) The /documents route colliding with the PDF static mount via the dev
proxy — renamed to /docfiles.

**Lessons:** keep domain logic framework-free (the `app/` layer survived
Streamlit → FastAPI untouched); make every pipeline idempotent before
making it scheduled; explainability is a feature users feel, not a nicety;
deterministic scoring beats LLM scoring wherever you must test it; "no
data" must never masquerade as "neutral".

---

# SECTION 23 — FUTURE ROADMAP

**V2 (product depth):** AI Insights page (themed insights w/ source+page+
confidence — table already exists), peer radar + composite score, credit
ratings + insider-trades ingestion, events calendar, portfolio transactions
/ XIRR / benchmark, combined market-board endpoint, golden-set RAG evals.
**V3 (platform):** auth + multi-user scoping, Postgres/Redis/Alembic,
WebSocket quotes, worker extraction, document upload UI, mobile PWA.
**Enterprise:** SSO, audit logs, role-based dashboards, compliance exports,
on-prem LLM option. **SaaS:** usage-metered billing, per-tenant vector
namespaces, broker integrations (paper→live behind approvals), SLA
observability. **AI-agent version:** planner over the existing tool surface
(screener→research→sentiment→alerts as tools) producing scheduled deep-dive
reports with human-in-the-loop checkpoints. **Multi-market:** BSE, then US
equities (exchange-aware symbology, currency layer, market-hours engine).

---

# APPENDIX — DIAGRAMS & CHEAT SHEETS

## A. Sequence — copilot question
```
UI          API              research.py           Gemini        Chroma      DB
 │ POST /research/chat │          │                  │             │          │
 │────────────────────►│ build_context()            │             │          │
 │                     │─────────────────────────────────────────────────────►│
 │                     │ retrieve(): embed(q) ──────►│             │          │
 │                     │            query/get ──────────────────►│           │
 │                     │            rerank ─────────►│             │          │
 │ ◄─SSE sources───────│                             │             │          │
 │                     │ generate_content_stream ───►│             │          │
 │ ◄─SSE delta ×N──────│◄─tokens─────────────────────│             │          │
 │ ◄─SSE done──────────│ save research_chat ─────────────────────────────────►│
```

## B. Deployment (current vs target)
```
NOW: one box — uvicorn(API+3 workers) + vite dev + SQLite + chroma_db/
TARGET: CloudFront(static React) → ALB → ECS api×N (stateless)
        ECS worker×1 (engine/alerts/etl) → RDS Postgres + ElastiCache
        S3 documents → Gemini/HF APIs; Secrets Manager; CloudWatch
```

## C. Quick-revision sheet
- **Stack:** React19/Vite7/TS/Tailwind4/TanStackQuery · FastAPI/Pydantic2 ·
  SQLAlchemy(SQLite→PG) · ChromaDB · Gemini(text/stream/embed) · FinBERT ·
  spaCy · rapidfuzz · yfinance · NSE NextApi.
- **Numbers:** 500 companies · 14 tables · 12 routers/~60 endpoints ·
  12 pages · 3 workers (60s/300s/daily) · 35 tests · chunks 1000/150 ·
  retrieval 18→20→k6 · context 9k/6k chars · weights 30/30/20/10/10 ·
  bands 20/40/60/80 · alert cooldown 24h · caches: quote 30s, corporate
  10m, screener/sentiment/backtest 10m, history 1h.
- **Signal rule:** positive>0.75 ∧ event∈{order_win, agreement_mou,
  earnings, securities_issuance} → BUY else HOLD.
- **War stories:** reload storm → scoped reload dirs; MACD noise floor;
  /documents vs /docfiles collision; Gemini 429 budgeting; IST = UTC-tagged
  serializer + pinned formatters.
- **One-liner:** *"Explainable AI equity research: every signal cites its
  headline, every score decomposes into factors, every answer cites its
  page."*

*— End of handbook —*
