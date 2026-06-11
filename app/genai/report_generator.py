"""L8 — AI investment report generation.

Assembles a stock's quantitative metrics (L4), fundamentals (L5), peer ranking
(L6) and recent news signals into a prompt, sends it to Gemini, and returns a
Markdown investment summary. Data assembly is separated from the network call so
it can be tested without an API key.
"""

import json

from app.analytics.analytics import analyze_symbol as quant_analyze
from app.analytics.competitor_analysis import compare_symbol
from app.analytics.financial_analysis import analyze_symbol as fin_analyze
from app.db.database import get_session
from app.db.models import Company, NewsSignal
from app.genai import gemini_client
from app.db.repository import save_report, get_latest_report

SYSTEM_INSTRUCTION = (
    "You are an experienced equity research analyst covering Indian (NSE) stocks. "
    "You write clear, balanced, evidence-based investment summaries for a retail "
    "audience. Ground every claim in the structured data provided — never invent "
    "numbers. If a metric is missing, say so rather than guessing. Be objective: "
    "cover both strengths and risks. Use Markdown with the section headings given. "
    "End with a clear, prominent disclaimer that this is an automated, educational "
    "summary and NOT financial advice."
)

REPORT_SECTIONS = [
    "Overview",
    "Valuation",
    "Growth & Profitability",
    "Technical / Quant",
    "Peer Positioning",
    "Risks",
    "Overall View",
]


def _recent_signals(symbol, limit=8):
    with get_session() as session:
        rows = (
            session.query(
                NewsSignal.source, NewsSignal.signal, NewsSignal.event,
                NewsSignal.sentiment_label, NewsSignal.news, NewsSignal.published_at,
            )
            .filter(NewsSignal.ticker == symbol)
            .order_by(NewsSignal.id.desc())
            .limit(limit)
            .all()
        )
    return [
        {
            "source": r[0], "signal": r[1], "event": r[2],
            "sentiment": r[3], "headline": (r[4] or "")[:200], "time": r[5],
        }
        for r in rows
    ]


def _company_name(symbol):
    with get_session() as session:
        c = session.query(Company).filter_by(symbol=symbol).first()
        return c.name if c else symbol


def build_context(symbol: str) -> dict:
    """Gather all available structured data for a stock."""
    return {
        "symbol": symbol,
        "company": _company_name(symbol),
        "quantitative_metrics": quant_analyze(symbol),
        "fundamentals": fin_analyze(symbol),
        "peer_comparison": compare_symbol(symbol),
        "recent_signals": _recent_signals(symbol),
    }


def build_prompt(context: dict) -> str:
    """Render the data context into a prompt for the report."""
    sections = "\n".join(f"- {s}" for s in REPORT_SECTIONS)
    data_json = json.dumps(context, indent=2, default=str)

    return (
        f"Write an investment summary for {context['company']} "
        f"({context['symbol']}) on the NSE.\n\n"
        f"Use ONLY the structured data below. Where a value is null or missing, "
        f"state that the data is unavailable instead of inventing it.\n\n"
        f"Structure the report with these Markdown sections (## headings):\n"
        f"{sections}\n\n"
        f"Keep it concise and readable (roughly 400-600 words). Quote the relevant "
        f"figures (returns, volatility, Sharpe, ROE, ROCE, P/E, peer ranks, recent "
        f"signals) to support each point.\n\n"
        f"=== STRUCTURED DATA ===\n{data_json}\n"
    )


def generate_report(symbol: str, use_cache: bool = True) -> dict:
    """Generate (or fetch cached) an AI investment report for a symbol.

    Returns {symbol, report_md, model, generated_at, cached}.
    """
    if use_cache:
        cached = get_latest_report(symbol)
        if cached:
            return {
                "symbol": symbol,
                "report_md": cached["content"],
                "model": cached["model"],
                "generated_at": cached["generated_at"],
                "cached": True,
            }

    context = build_context(symbol)
    prompt = build_prompt(context)

    report_md = gemini_client.generate_text(
        prompt, system_instruction=SYSTEM_INSTRUCTION
    )

    from app.config import GEMINI_MODEL
    save_report(symbol, report_md, GEMINI_MODEL)

    return {
        "symbol": symbol,
        "report_md": report_md,
        "model": GEMINI_MODEL,
        "generated_at": None,
        "cached": False,
    }
