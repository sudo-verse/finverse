---
title: Finverse
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
---

# Finverse — AI-Powered Stock Market Intelligence

An end-to-end NSE (India) market intelligence platform: multi-source news →
FinBERT sentiment → trade signals, plus a relational data warehouse, quantitative
& fundamental analytics, competitor comparison, AI investment reports (Gemini),
RAG document Q&A, and a portfolio dashboard.

## Architecture (layers)

| Layer | What it does | Key modules |
|------|--------------|-------------|
| Storage (L2) | SQLAlchemy ORM, SQLite-now/MySQL-ready | `app/db/` |
| ETL (L3) | Companies, prices (yfinance), fundamentals, signals | `app/etl/` |
| Analytics (L4) | Returns, volatility, Sharpe, MAs, trend | `app/analytics/metrics.py`, `analytics.py` |
| Financials (L5) | Revenue growth, margins, ROE/ROCE, P/E, P/B | `app/analytics/financial_analysis.py` |
| Competitors (L6) | Industry peer comparison & ranking | `app/analytics/competitor_analysis.py` |
| News (L7) | Multi-source ingestion + FinBERT sentiment + signals | `app/ingestion/`, `app/nlp/`, `app/main_nse.py` |
| AI Reports (L8) | Gemini-written investment summaries | `app/genai/report_generator.py` |
| RAG (L9) | ChromaDB + Gemini Q&A over filings | `app/genai/rag.py` |
| Dashboard (L10) | Streamlit multi-tab UI | `app.py` |
| Portfolio (L11) | Value, P&L, allocation, diversification, risk | `app/analytics/portfolio.py` |
| Deployment (L12) | Streamlit Cloud / Render | this section |

## Local setup

```bash
# Dashboard only (slim):
pip install -r requirements.txt

# Full stack (engine + ETL: FinBERT, spaCy, scrapers):
pip install -r requirements-engine.txt
python -m spacy download en_core_web_sm
```

Create `.env` (see keys below), then:

```bash
python -m app.etl.run_etl          # populate companies + prices + signals
streamlit run app.py               # launch the dashboard
python -m app.main_nse             # (optional) run the real-time signal engine
```

### Environment variables

| Var | Purpose |
|-----|---------|
| `GEMINI_API_KEY` | AI reports (L8) + RAG (L9) |
| `GEMINI_MODEL` | default `gemini-2.5-flash` |
| `DATABASE_URL` | default `sqlite:///finverse.db`; MySQL e.g. `mysql+pymysql://user:pass@host:3306/finverse` |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | optional, engine alerts |

## Deployment

The **dashboard** deploys slim — `requirements.txt` deliberately excludes
torch/transformers/spaCy (they'd exceed Streamlit Cloud's resource limits). The
FinBERT/spaCy **engine runs separately** and writes to the shared database.

### Streamlit Community Cloud
1. Push to GitHub.
2. New app → point at `app.py`.
3. Add secrets (copy `.streamlit/secrets.toml.example`) — at minimum `GEMINI_API_KEY`.
   Streamlit exposes secrets as env vars, so `app/config.py` reads them via `os.getenv`.
4. SQLite is **ephemeral** on Cloud (resets on reboot). For persistence set
   `DATABASE_URL` to a hosted MySQL, then seed it with `python -m app.etl.run_etl`.

### Render
Uses `Procfile` + `runtime.txt`:
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```
Set the same env vars in the Render dashboard.

### Seeding data
`app.py` creates the tables on first run. To populate a fresh deploy's database,
run the ETL against the same `DATABASE_URL`:
```bash
python -m app.etl.run_etl --prices 1y      # full
python -m app.etl.run_etl --skip-prices    # quick (companies + signals only)
```

> Educational project — not financial advice.
