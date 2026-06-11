"""Signal performance backtesting — does the engine's advice actually work?

For every BUY/SELL signal with a resolvable company, compute the forward
price return over 7 and 30 calendar days from `price_history` (nearest
trading day at or before each target date). A signal "hits" when the move
matches its direction. HOLD signals are excluded — they make no claim.

Honest-measurement notes:
  - signals younger than 7 days are excluded (no forward window yet)
  - 30d stats only include signals old enough to have a 30d window
  - returns are simple close-to-close, no costs/slippage
"""

import time
from datetime import timedelta

from sqlalchemy.orm import Session

from app.db.models import NewsSignal, PriceHistory
from backend.schemas.signal_perf import SignalExample, SignalPerformance, SignalPerfRow

_cache: tuple[float, SignalPerformance] | None = None
CACHE_TTL = 600


def _forward_return(closes: dict, dates: list, signal_date, days: int):
    """Return over `days` from the first trading day >= signal date."""
    import bisect

    start_i = bisect.bisect_left(dates, signal_date)
    if start_i >= len(dates):
        return None
    target = signal_date + timedelta(days=days)
    end_i = bisect.bisect_right(dates, target) - 1
    if end_i <= start_i:
        return None
    start, end = closes[dates[start_i]], closes[dates[end_i]]
    if not start or not end:
        return None
    # the window must actually span (mostly) the horizon, not 2 days of it
    if (dates[end_i] - dates[start_i]).days < days * 0.6:
        return None
    return end / start - 1


def compute_performance(session: Session) -> SignalPerformance:
    global _cache
    if _cache and time.time() - _cache[0] < CACHE_TTL:
        return _cache[1]

    from datetime import date

    today = date.today()
    signals = (
        session.query(NewsSignal)
        .filter(NewsSignal.company_id.isnot(None),
                NewsSignal.signal.in_(["BUY", "SELL"]))
        .all()
    )
    # price series per company involved, one query
    company_ids = {s.company_id for s in signals}
    series: dict[int, tuple] = {}
    if company_ids:
        rows = (
            session.query(PriceHistory.company_id, PriceHistory.date, PriceHistory.close)
            .filter(PriceHistory.company_id.in_(company_ids))
            .order_by(PriceHistory.date)
            .all()
        )
        tmp: dict[int, dict] = {}
        for cid, d, close in rows:
            tmp.setdefault(cid, {})[d] = close
        series = {cid: (closes, sorted(closes)) for cid, closes in tmp.items()}

    stats = {"BUY": {"r7": [], "r30": []}, "SELL": {"r7": [], "r30": []}}
    examples: list[SignalExample] = []
    evaluated = 0
    for s in signals:
        if s.created_at is None or s.company_id not in series:
            continue
        sig_date = s.created_at.date()
        age = (today - sig_date).days
        if age < 7:
            continue  # too young to judge
        closes, dates = series[s.company_id]
        r7 = _forward_return(closes, dates, sig_date, 7)
        r30 = _forward_return(closes, dates, sig_date, 30) if age >= 30 else None
        if r7 is None and r30 is None:
            continue
        evaluated += 1
        if r7 is not None:
            stats[s.signal]["r7"].append(r7)
        if r30 is not None:
            stats[s.signal]["r30"].append(r30)
        best = r30 if r30 is not None else r7
        examples.append(SignalExample(
            symbol=s.ticker, signal=s.signal, date=str(sig_date),
            return_pct=best, headline=(s.news or "")[:120],
        ))

    def row(name: str) -> SignalPerfRow:
        r7, r30 = stats[name]["r7"], stats[name]["r30"]
        sign = 1 if name == "BUY" else -1
        hits = [x for x in (r30 or r7) if sign * x > 0]
        base = r30 or r7
        return SignalPerfRow(
            signal=name,
            count=len(base),
            hit_rate=len(hits) / len(base) if base else None,
            avg_return_7d=sum(r7) / len(r7) if r7 else None,
            avg_return_30d=sum(r30) / len(r30) if r30 else None,
        )

    examples.sort(key=lambda e: -(e.return_pct or 0))
    out = SignalPerformance(
        evaluated=evaluated,
        rows=[row("BUY"), row("SELL")],
        best=examples[:3],
        worst=list(reversed(examples[-3:])) if len(examples) > 3 else [],
    )
    _cache = (time.time(), out)
    return out
