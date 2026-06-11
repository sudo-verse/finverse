"""Dashboard aggregates: counts, distributions and trend over `news_signals`,
plus the portfolio headline number via the portfolio service.

Mirrors the Streamlit overview tab (`app.py` header + tab_overview) as SQL
aggregations instead of in-memory pandas.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Company, NewsSignal, PriceHistory
from backend.schemas.dashboard import (
    DashboardMetrics,
    DashboardOut,
    DistributionItem,
    IndustryCount,
    NewsEventOut,
    TrendPoint,
)
from backend.services.portfolio_service import portfolio_service
from backend.services.signal_service import base_signal_query, row_to_signal

logger = logging.getLogger("finverse.api")

TREND_DAYS = 14
RECENT_LIMIT = 6
TOP_INDUSTRIES = 8


class DashboardService:
    def get_dashboard(self, session: Session) -> DashboardOut:
        # --- Signal distribution (one grouped query feeds counts + chart) ---
        dist_rows = (
            session.query(NewsSignal.signal, func.count(NewsSignal.id))
            .group_by(NewsSignal.signal)
            .all()
        )
        by_signal = {(sig or "UNKNOWN"): n for sig, n in dist_rows}
        total_signals = sum(by_signal.values())

        portfolio_value, portfolio_day_change_pct = portfolio_service.portfolio_value()

        metrics = DashboardMetrics(
            total_companies=session.query(func.count(Company.id)).scalar() or 0,
            total_signals=total_signals,
            buy_signals=by_signal.get("BUY", 0),
            sell_signals=by_signal.get("SELL", 0),
            hold_signals=by_signal.get("HOLD", 0),
            price_rows=session.query(func.count(PriceHistory.id)).scalar() or 0,
            portfolio_value=portfolio_value,
            portfolio_day_change_pct=portfolio_day_change_pct,
        )

        # --- Industry distribution of signals ---
        industry_rows = (
            session.query(Company.industry, func.count(NewsSignal.id))
            .join(NewsSignal, NewsSignal.company_id == Company.id)
            .filter(Company.industry.isnot(None))
            .group_by(Company.industry)
            .order_by(func.count(NewsSignal.id).desc())
            .limit(TOP_INDUSTRIES)
            .all()
        )

        # --- Daily trend (last TREND_DAYS days) ---
        since = datetime.utcnow() - timedelta(days=TREND_DAYS)
        day = func.date(NewsSignal.created_at)
        trend_rows = (
            session.query(day, NewsSignal.signal, func.count(NewsSignal.id))
            .filter(NewsSignal.created_at >= since)
            .group_by(day, NewsSignal.signal)
            .order_by(day)
            .all()
        )
        trend: dict[str, dict[str, int]] = {}
        for d, sig, n in trend_rows:
            bucket = trend.setdefault(str(d), {"BUY": 0, "SELL": 0, "HOLD": 0})
            if sig in bucket:
                bucket[sig] = n

        # --- Recent activity ---
        recent_rows = (
            base_signal_query(session).order_by(NewsSignal.id.desc()).limit(RECENT_LIMIT).all()
        )
        recent_signals = [row_to_signal(r) for r in recent_rows]
        recent_news = [
            NewsEventOut(
                id=s.id,
                symbol=s.symbol,
                headline=s.event_title,
                source=s.source,
                sentiment=s.sentiment,
                timestamp=s.timestamp,
            )
            for s in recent_signals
        ]

        return DashboardOut(
            metrics=metrics,
            signal_distribution=[
                DistributionItem(name=k, value=v)
                for k, v in sorted(by_signal.items(), key=lambda kv: -kv[1])
            ],
            industry_distribution=[
                IndustryCount(industry=ind, count=n) for ind, n in industry_rows
            ],
            daily_signal_trend=[
                TrendPoint(date=d, buy=c["BUY"], sell=c["SELL"], hold=c["HOLD"])
                for d, c in sorted(trend.items())
            ],
            recent_signals=recent_signals,
            recent_news=recent_news,
        )


dashboard_service = DashboardService()
