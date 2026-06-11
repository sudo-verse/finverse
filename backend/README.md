# Finverse API (FastAPI)

REST layer between the React frontend (`frontend/`) and the existing Finverse
engine (`app/`). It contains **no business logic** — every endpoint delegates
to the existing analytics/genai modules and only shapes the result.

## Run

```bash
pip install -r requirements-api.txt
python -m uvicorn backend.main:app --reload --port 8000 \
  --reload-dir app --reload-dir backend --reload-include '*.py'
```

> The `--reload-dir` flags matter: the embedded news engine writes
> `signals.json` / `finverse.db` in the repo root, and letting the reloader
> watch the whole tree makes every ingested article restart the server.

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health: http://localhost:8000/health

Tables are created automatically on startup (`app.db.init_db`). Populate data
with the existing pipelines: `python -m app.etl.run_etl` (companies, prices,
financials). AI report and chat endpoints need `GEMINI_API_KEY` in `.env`.

A **daily data refresh** also runs inside the API: prices top-up every day at
`BACKEND_ETL_HOUR_IST` (default 18:30 IST, post market close), company master +
financials weekly on Sundays, plus a catch-up run on startup if prices are
stale. Disable with `BACKEND_ETL_ENABLED=false`.

The real-time news engine runs **inside the API** as a background worker
(every `BACKEND_ENGINE_INTERVAL` seconds, default 60) — no separate process
needed. Watch it at `GET /api/engine/status`. To run the standalone engine
(`python -m app.main_nse`) instead, set `BACKEND_ENGINE_ENABLED=false`.

## Endpoint → module mapping

| Endpoint | Delegates to |
| --- | --- |
| `GET /api/dashboard` | SQL aggregates over `news_signals` / `companies` / `price_history` + `app.analytics.portfolio.compute_portfolio` |
| `GET /api/signals` | `news_signals` table (SQL-level filter + paginate) |
| `GET /api/signals/facets` | distinct values from `news_signals` |
| `GET /api/stocks` | `companies` table |
| `GET /api/stocks/{symbol}` | `app.analytics.analytics.load_prices`, `app.analytics.metrics` (`compute_all`, `moving_average`), `app.analytics.financial_analysis.analyze_symbol` |
| `GET /api/competitors/{symbol}` | `app.analytics.competitor_analysis` (`get_peers`, `compare_symbol`, `compare_industry`) |
| `GET /api/portfolio` | `app.analytics.portfolio.compute_portfolio`, `app.db.repository.list_holdings` |
| `POST /api/portfolio/holdings` | `app.db.repository.add_holding` |
| `DELETE /api/portfolio/holdings` | `app.db.repository.clear_holdings` |
| `POST /api/report` | `app.genai.report_generator.generate_report` (Gemini + DB cache) |
| `POST /api/chat` | `app.genai.rag.answer_question` (ChromaDB + Gemini) |
| `POST /api/research/chat` | `app.genai.research.research_answer` (hybrid RAG + rerank + Gemini, SSE streaming) + `app.genai.report_generator.build_context` |
| `POST /api/research/compare` | `app.genai.research.research_compare` (per-company retrieval, comparison report) |
| `GET /api/research/companies` | `companies` table + ChromaDB chunk counts |
| `GET /api/research/sources/{symbol}` | `app.genai.research.source_summary` + DB availability checks |
| `GET /api/research/history` | `research_chats` table (`app.db.repository`) |

All responses are camelCase (Pydantic alias generator) to match the frontend's
TypeScript interfaces.

## curl examples

```bash
# Health
curl http://localhost:8000/health

# Dashboard aggregates
curl http://localhost:8000/api/dashboard

# Signals — paginated + filtered
curl "http://localhost:8000/api/signals?page=1&pageSize=12"
curl "http://localhost:8000/api/signals?signal=BUY&sentiment=positive"
curl "http://localhost:8000/api/signals?source=Moneycontrol&search=reliance"

# Filter dropdown values
curl http://localhost:8000/api/signals/facets

# Companies
curl "http://localhost:8000/api/stocks"
curl "http://localhost:8000/api/stocks?search=tata&limit=10"

# Full stock analysis (history window configurable)
curl "http://localhost:8000/api/stocks/TCS"
curl "http://localhost:8000/api/stocks/TCS?historyDays=90"

# Peer comparison
curl http://localhost:8000/api/competitors/TCS

# Portfolio
curl -X POST http://localhost:8000/api/portfolio/holdings \
  -H 'Content-Type: application/json' \
  -d '{"symbol": "TCS", "quantity": 50, "avgPrice": 2900}'
curl http://localhost:8000/api/portfolio
curl -X DELETE http://localhost:8000/api/portfolio/holdings

# AI investment report (Gemini; useCache=false forces regeneration)
curl -X POST http://localhost:8000/api/report \
  -H 'Content-Type: application/json' \
  -d '{"symbol": "TCS", "useCache": true}'

# RAG document Q&A (optionally scoped to a symbol)
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What does the annual report say about margins?", "symbol": null, "k": 4}'

# AI Research Copilot — company-aware chat (SSE stream; "stream": false for JSON)
curl -N -X POST http://localhost:8000/api/research/chat \
  -H 'Content-Type: application/json' \
  -d '{"symbol": "RELIANCE", "message": "What are the biggest risks?", "stream": true}'

# Compare two companies
curl -X POST http://localhost:8000/api/research/compare \
  -H 'Content-Type: application/json' \
  -d '{"symbols": ["TCS", "INFY"], "stream": false}'

# Researchable companies / available sources / past Q&A
curl "http://localhost:8000/api/research/companies?search=tata"
curl http://localhost:8000/api/research/sources/RELIANCE
curl "http://localhost:8000/api/research/history?limit=10"
```

## Configuration

HTTP-layer settings use the `BACKEND_` env prefix (see `backend/core/config.py`):

```bash
BACKEND_CORS_ORIGINS=http://localhost:5173,https://finverse.example.com
BACKEND_DEFAULT_PAGE_SIZE=12
```

Domain settings (DATABASE_URL, GEMINI_API_KEY, CHROMA_DIR…) stay in
`app/config.py` / `.env` as before.

## Connecting the React frontend

`frontend/vite.config.ts` already proxies `/api` to `http://localhost:8000`.
To switch off mock data:

```bash
cd frontend
echo "VITE_USE_MOCKS=false" > .env
npm run dev
```
