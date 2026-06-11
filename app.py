"""Finverse — Market Intelligence Dashboard (Streamlit).

A read/visualize layer over the Finverse database. The real-time engine
(`python -m app.main_nse`) and the ETL pipeline (`python -m app.etl.run_etl`)
populate the data; this app surfaces it.
"""

import pandas as pd
import streamlit as st

from app.analytics import metrics as M
from app.analytics.analytics import analyze_symbol as quant_analyze, load_prices
from app.analytics.competitor_analysis import compare_industry, compare_symbol
from app.analytics.financial_analysis import analyze_symbol as fin_analyze
from app.db.database import get_session
from app.db.models import Company, NewsSignal, PriceHistory
from app.db.repository import get_latest_report
from app.genai import gemini_client
from app.genai.report_generator import generate_report

st.set_page_config(page_title="Finverse", page_icon="📊", layout="wide")


@st.cache_resource
def _ensure_db():
    """Create tables on first run so a fresh deploy works out of the box."""
    from app.db.init_db import init_db
    init_db()
    return True


_ensure_db()


# --------------------------------------------------------------------------
# Data access (cached)
# --------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_signals() -> pd.DataFrame:
    with get_session() as s:
        rows = (
            s.query(
                NewsSignal.created_at, NewsSignal.source, NewsSignal.ticker,
                NewsSignal.signal, NewsSignal.event, NewsSignal.sentiment_label,
                NewsSignal.sentiment_score, NewsSignal.price, NewsSignal.news,
                NewsSignal.published_at, Company.name.label("company"),
            )
            .outerjoin(Company, NewsSignal.company_id == Company.id)
            .order_by(NewsSignal.id.desc())
            .all()
        )
    return pd.DataFrame(rows, columns=[
        "created_at", "source", "ticker", "signal", "event", "sentiment",
        "score", "price", "news", "published_at", "company",
    ])


@st.cache_data(ttl=300)
def symbols_with_prices() -> list:
    with get_session() as s:
        rows = (
            s.query(Company.symbol)
            .join(PriceHistory, PriceHistory.company_id == Company.id)
            .distinct().order_by(Company.symbol).all()
        )
    return [r[0] for r in rows]


@st.cache_data(ttl=300)
def industries_with_data() -> list:
    with get_session() as s:
        rows = (
            s.query(Company.industry)
            .filter(Company.industry.isnot(None))
            .distinct().order_by(Company.industry).all()
        )
    return [r[0] for r in rows]


@st.cache_data(ttl=300)
def db_counts() -> dict:
    with get_session() as s:
        return {
            "companies": s.query(Company).count(),
            "prices": s.query(PriceHistory).count(),
            "signals": s.query(NewsSignal).count(),
        }


@st.cache_data(ttl=120)
def price_with_mas(symbol: str) -> pd.DataFrame:
    df = load_prices(symbol)
    if df.empty:
        return df
    out = pd.DataFrame({"close": df["close"]})
    for w in (20, 50, 200):
        if len(df) >= w:
            out[f"SMA{w}"] = M.moving_average(df["close"], w, "sma")
    return out


def pct(x):
    return f"{x*100:.1f}%" if isinstance(x, (int, float)) else "—"


def num(x, p=2):
    return f"{x:,.{p}f}" if isinstance(x, (int, float)) else "—"


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.title("📊 Finverse — Market Intelligence")
counts = db_counts()
if sum(counts.values()) == 0:
    st.warning(
        "No data yet. Run the ETL first:  `python -m app.etl.run_etl`  "
        "and/or the engine:  `python -m app.main_nse`"
    )

signals_df = load_signals()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Companies", f"{counts['companies']:,}")
c2.metric("Price rows", f"{counts['prices']:,}")
c3.metric("Signals", f"{counts['signals']:,}")
buys = int((signals_df["signal"] == "BUY").sum()) if not signals_df.empty else 0
c4.metric("BUY signals", f"{buys:,}")

tab_overview, tab_signals, tab_stock, tab_peers, tab_portfolio, tab_docs = st.tabs(
    ["📈 Overview", "🔔 Signals", "🔍 Stock Analysis", "🏭 Competitors",
     "💼 Portfolio", "📚 Docs Q&A"]
)

# --------------------------------------------------------------------------
# Overview
# --------------------------------------------------------------------------
with tab_overview:
    if signals_df.empty:
        st.info("No signals yet — start the engine with `python -m app.main_nse`.")
    else:
        left, right = st.columns(2)
        with left:
            st.subheader("Signal distribution")
            st.bar_chart(signals_df["signal"].value_counts())
        with right:
            st.subheader("Signals by source")
            st.bar_chart(signals_df["source"].value_counts())

        st.subheader("🧠 Latest signals")
        st.dataframe(
            signals_df[["created_at", "source", "company", "ticker", "signal",
                        "event", "sentiment", "score", "price"]].head(15),
            width="stretch", hide_index=True,
        )

# --------------------------------------------------------------------------
# Signals (filterable feed)
# --------------------------------------------------------------------------
with tab_signals:
    if signals_df.empty:
        st.info("No signals to filter yet.")
    else:
        f1, f2, f3 = st.columns(3)
        sig_opt = f1.multiselect("Signal", sorted(signals_df["signal"].dropna().unique()))
        src_opt = f2.multiselect("Source", sorted(signals_df["source"].dropna().unique()))
        query = f3.text_input("Search company / ticker")

        view = signals_df
        if sig_opt:
            view = view[view["signal"].isin(sig_opt)]
        if src_opt:
            view = view[view["source"].isin(src_opt)]
        if query:
            q = query.lower()
            view = view[
                view["company"].fillna("").str.lower().str.contains(q)
                | view["ticker"].fillna("").str.lower().str.contains(q)
            ]

        st.caption(f"{len(view)} of {len(signals_df)} signals")
        st.dataframe(
            view[["created_at", "source", "company", "ticker", "signal", "event",
                  "sentiment", "score", "price", "news"]],
            width="stretch", hide_index=True,
        )

# --------------------------------------------------------------------------
# Stock Analysis (L4 + L5)
# --------------------------------------------------------------------------
with tab_stock:
    syms = symbols_with_prices()
    if not syms:
        st.info("No price history yet. Run `python -m app.etl.run_etl`.")
    else:
        symbol = st.selectbox("Select a stock", syms)

        st.subheader(f"Price & moving averages — {symbol}")
        chart_df = price_with_mas(symbol)
        if chart_df.empty:
            st.info("No price data for this symbol.")
        else:
            st.line_chart(chart_df)

        q = quant_analyze(symbol)
        if "error" not in q:
            st.subheader("📊 Quantitative metrics (L4)")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Latest price", num(q.get("latest_price")))
            m2.metric("Cumulative return", pct(q.get("cumulative_return")))
            m3.metric("Volatility (ann.)", pct(q.get("annualized_volatility")))
            m4.metric("Sharpe", num(q.get("sharpe_ratio")))
            m5, m6, m7, m8 = st.columns(4)
            m5.metric("Max drawdown", pct(q.get("max_drawdown")))
            m6.metric("Trend", str(q.get("trend")))
            m7.metric("SMA 50", num(q.get("sma_50")))
            m8.metric("SMA 200", num(q.get("sma_200")))
        else:
            st.caption("No quantitative metrics (insufficient price history).")

        f = fin_analyze(symbol)
        if "error" not in f:
            st.subheader("💰 Financial ratios (L5)")
            n1, n2, n3, n4 = st.columns(4)
            n1.metric("Revenue growth", pct(f.get("revenue_growth")))
            n2.metric("Net margin", pct(f.get("net_profit_margin")))
            n3.metric("ROE", pct(f.get("roe")))
            n4.metric("ROCE", pct(f.get("roce")))
            o1, o2, o3, o4 = st.columns(4)
            o1.metric("Debt / Equity", num(f.get("debt_to_equity")))
            o2.metric("P/E", num(f.get("pe_ratio")))
            o3.metric("P/B", num(f.get("pb_ratio")))
            o4.metric("EPS", num(f.get("eps")))
        else:
            st.caption("No fundamentals loaded for this symbol "
                       "(`python -m app.etl.financials_etl`).")

        if not signals_df.empty:
            stock_sig = signals_df[signals_df["ticker"] == symbol]
            if not stock_sig.empty:
                st.subheader("🔔 Recent signals for this stock")
                st.dataframe(
                    stock_sig[["created_at", "source", "signal", "event",
                               "sentiment", "score", "news"]].head(10),
                    width="stretch", hide_index=True,
                )

        # --- AI investment report (L8) ---
        st.subheader("📝 AI Investment Report (L8)")
        if not gemini_client.is_configured():
            st.caption("Set GEMINI_API_KEY in .env to enable AI reports.")
        else:
            existing = get_latest_report(symbol)
            c_gen, c_info = st.columns([1, 3])
            gen = c_gen.button("Generate report", key=f"gen_{symbol}")
            regen = False
            if existing:
                c_info.caption(f"Cached report · {existing['generated_at']} · {existing['model']}")
                regen = c_info.button("Regenerate", key=f"regen_{symbol}")

            if gen or regen:
                with st.spinner("Generating report with Gemini…"):
                    try:
                        result = generate_report(symbol, use_cache=not regen)
                        st.markdown(result["report_md"])
                    except Exception as e:
                        st.error(f"Report generation failed: {e}")
            elif existing:
                st.markdown(existing["content"])

# --------------------------------------------------------------------------
# Competitors (L6)
# --------------------------------------------------------------------------
with tab_peers:
    inds = industries_with_data()
    if not inds:
        st.info("No company/industry data yet.")
    else:
        default_idx = inds.index("Information Technology") if "Information Technology" in inds else 0
        industry = st.selectbox("Industry", inds, index=default_idx)

        rows = compare_industry(industry)
        if not rows:
            st.info("No analytics/fundamentals available for this industry yet.")
        else:
            peer_df = pd.DataFrame(rows)
            cols = [c for c in [
                "symbol", "company", "revenue_growth", "net_profit_margin",
                "roe", "roce", "debt_to_equity", "pe_ratio", "pb_ratio",
                "cumulative_return", "sharpe_ratio",
            ] if c in peer_df.columns]
            st.subheader(f"{industry} — peer comparison")
            st.dataframe(peer_df[cols], width="stretch", hide_index=True)

            symbol = st.selectbox("Rank a stock vs peers", peer_df["symbol"].tolist())
            res = compare_symbol(symbol)
            if "error" not in res:
                st.caption(f"{res['company']} — ranked against {res['peer_count']} peers (1 = best)")
                rank_rows = [
                    {"metric": k, "value": v["value"],
                     "peer_avg": v["peer_avg"],
                     "rank": f"{v['rank']}/{v['out_of']}" if v["rank"] else "—"}
                    for k, v in res["comparison"].items()
                ]
                st.dataframe(pd.DataFrame(rank_rows), width="stretch", hide_index=True)

# --------------------------------------------------------------------------
# Portfolio (L11)
# --------------------------------------------------------------------------
with tab_portfolio:
    from app.analytics.portfolio import compute_portfolio
    from app.db.repository import add_holding, clear_holdings

    with st.expander("➕ Add / manage holdings"):
        with st.form("add_holding", clear_on_submit=True):
            cols = st.columns([2, 1, 1, 1])
            h_sym = cols[0].selectbox("Symbol", symbols_with_prices())
            h_qty = cols[1].number_input("Quantity", min_value=0.0, value=10.0, step=1.0)
            h_px = cols[2].number_input("Avg buy price", min_value=0.0, value=0.0, step=1.0)
            cols[3].markdown("&nbsp;")
            if cols[3].form_submit_button("Add"):
                add_holding(h_sym, h_qty, h_px or None)
                st.success(f"Added {h_qty:g} × {h_sym}")
        if st.button("Clear portfolio"):
            clear_holdings()
            st.warning("Portfolio cleared")

    p = compute_portfolio()
    if "error" in p:
        st.info("No holdings yet — add some above to see portfolio analytics.")
    else:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Portfolio value", num(p["total_value"], 0))
        k2.metric("Total P&L", num(p["total_pnl"], 0),
                  delta=pct(p["total_pnl_pct"]) if p["total_pnl_pct"] is not None else None)
        k3.metric("Volatility (ann.)", pct(p["annualized_volatility"]))
        k4.metric("Sharpe", num(p["sharpe_ratio"]))

        d1, d2, d3 = st.columns(3)
        d1.metric("Holdings", p["num_holdings"])
        d2.metric("Effective holdings", num(p["effective_holdings"], 1))
        d3.metric("Top concentration", pct(p["top_concentration"]))

        st.subheader("Holdings")
        hdf = pd.DataFrame(p["holdings"])
        show = [c for c in ["symbol", "industry", "quantity", "avg_price", "price",
                            "value", "weight", "pnl", "pnl_pct"] if c in hdf.columns]
        st.dataframe(hdf[show], width="stretch", hide_index=True)

        a1, a2 = st.columns(2)
        with a1:
            st.subheader("Allocation by stock")
            alloc = hdf[["symbol", "value"]].dropna().set_index("symbol")["value"]
            st.bar_chart(alloc)
        with a2:
            st.subheader("Allocation by sector")
            sec = pd.Series(p["sector_allocation"]) * 100
            st.bar_chart(sec)

# --------------------------------------------------------------------------
# Docs Q&A — RAG (L9)
# --------------------------------------------------------------------------
with tab_docs:
    st.subheader("📚 Document Q&A (RAG)")
    if not gemini_client.is_configured():
        st.caption("Set GEMINI_API_KEY in .env to enable document Q&A.")
    else:
        from app.genai import rag

        st.caption(f"Knowledge base: {rag.stats()['chunks']} chunks indexed")

        with st.expander("➕ Ingest a document (annual report, filing, transcript)"):
            up = st.file_uploader("Upload a PDF or text file", type=["pdf", "txt"])
            doc_symbol = st.text_input("Tag with symbol (optional)", "")
            if up is not None and st.button("Ingest"):
                import tempfile, os as _os
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=_os.path.splitext(up.name)[1]
                ) as tmp:
                    tmp.write(up.getvalue())
                    tmp_path = tmp.name
                with st.spinner("Embedding & indexing…"):
                    try:
                        n = rag.ingest_file(tmp_path, symbol=doc_symbol or None)
                        st.success(f"Ingested {n} chunks from {up.name}")
                    except Exception as e:
                        st.error(f"Ingestion failed: {e}")
                    finally:
                        _os.unlink(tmp_path)

        question = st.text_input("Ask a question about the documents")
        q_symbol = st.text_input("Filter to symbol (optional)", "")
        if question and st.button("Ask"):
            with st.spinner("Searching documents & answering…"):
                try:
                    res = rag.answer_question(question, symbol=q_symbol or None)
                    st.markdown(res["answer"])
                    if res["sources"]:
                        st.caption("Sources")
                        for s in res["sources"]:
                            st.markdown(f"**{s['source']}** — _{s['snippet']}…_")
                except Exception as e:
                    st.error(f"Q&A failed: {e}")

st.caption("Finverse · data via NSE/Yahoo/news feeds · FinBERT sentiment · SQLAlchemy-backed")
