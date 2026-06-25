"""Market-wide corporate-announcements feed.

NSE's `corporate-announcements?index=equities` returns the latest exchange
filings across the whole market (≈3k over a couple of days). We fetch a short
date window through the warmed NSE session (Mumbai-IP only, same path as the
deals/events ETLs), classify each into an investor-facing bucket — orders,
ratings, fund-raising, results, M&A, dividends, … — and cache ~5 min.

Order/rating/fund-raise intent lives in the attachment text, so we keyword-scan
`desc + attchmntText` first, then fall back to NSE's own `desc` vocabulary.
Routine noise (trading-window closures, newspaper copies) is bucketed as
"routine" and hidden unless asked for.
"""

import time
from datetime import date, timedelta

from backend.schemas.announcements import AnnouncementFeedRow

_URL = "https://www.nseindia.com/api/corporate-announcements"
_CACHE_TTL = 300
_cache: dict[int, tuple[float, list[AnnouncementFeedRow]]] = {}

# High-signal keyword buckets, checked in priority order over desc + text.
_KEYWORD_CATS: list[tuple[str, tuple[str, ...]]] = [
    ("result", ("financial result", "quarterly result", "unaudited result",
                "audited result", "results for the quarter", "clarification - financial",
                "clarification- financial", "financial results")),
    ("order", ("work order", "purchase order", "letter of intent", "letter of award",
               "bags ", "bagged", "awarded", "awarding", "secures order", "wins order",
               "receipt of order", "new order", "order win", "order worth", "contract")),
    ("rating", ("credit rating", "rating action", "icra", "crisil", "care ratings",
                "ind-ra", "india ratings", "rating revised", "rating reaffirmed",
                "rating upgrade", "rating downgrade", "assigns rating")),
    ("fundraise", ("fund rais", "fundrais", "raising of funds", "issue of securities",
                   "preferential issue", "preferential allotment", "qualified institutional",
                   "qip", "rights issue", "non-convertible debenture", "issue of ncd",
                   "commercial paper", "issuance of bonds", "raising funds")),
    ("dividend", ("dividend",)),
    ("buyback", ("buyback", "buy-back", "buy back")),
    ("mna", ("acquisition", "amalgamation", "scheme of arrangement", "slump sale",
             "divestment", "stake sale", "merger", "to acquire")),
]

# NSE `desc` label substring → bucket (fallback when no keyword hits).
_DESC_MAP: list[tuple[str, str]] = [
    ("takeover", "sast"),
    ("board meeting", "board"),
    ("shareholders meeting", "agm"),
    ("appointment", "management"),
    ("resignation", "management"),
    ("change in director", "management"),
    ("analyst", "investor"),
    ("investor", "investor"),
    ("con. call", "investor"),
    ("conference call", "investor"),
    ("trading window", "routine"),
    ("newspaper", "routine"),
    ("spurt in volume", "routine"),
    ("regulation 30", "routine"),
]

_ROUTINE = {"routine"}


def _classify(desc: str, text: str) -> str:
    blob = f"{desc} {text}".lower()
    for cat, kws in _KEYWORD_CATS:
        if any(k in blob for k in kws):
            return cat
    dl = desc.lower()
    for sub, cat in _DESC_MAP:
        if sub in dl:
            return cat
    if "annual general meeting" in blob or "postal ballot" in blob or "extraordinary general" in blob:
        return "agm"
    return "other"


def _fetch_window(days: int) -> list[AnnouncementFeedRow]:
    from app.market import nse_shp

    to_d = date.today()
    from_d = to_d - timedelta(days=days)
    params = {
        "index": "equities",
        "from_date": from_d.strftime("%d-%m-%Y"),
        "to_date": to_d.strftime("%d-%m-%Y"),
    }
    data = None
    for attempt in range(2):
        try:
            r = nse_shp._sess().get(_URL, params=params, timeout=25)
            if r.status_code == 200:
                data = r.json()
                break
            nse_shp._sess().get(nse_shp._HOME, timeout=10)  # refresh stale cookies
        except Exception:
            try:
                nse_shp._sess().get(nse_shp._HOME, timeout=10)
            except Exception:
                pass
    rows = data if isinstance(data, list) else (data or {}).get("data", [])

    out: list[AnnouncementFeedRow] = []
    for r in rows or []:
        desc = (r.get("desc") or "").strip()
        detail = (r.get("attchmntText") or "").strip()
        sort_date = (r.get("sort_date") or "").strip()
        out.append(AnnouncementFeedRow(
            symbol=(r.get("symbol") or "").strip().upper() or None,
            name=(r.get("sm_name") or "").strip() or None,
            category=_classify(desc, detail),
            desc=desc or None,
            detail=detail[:600] or None,
            broadcast_at=sort_date.replace(" ", "T") or None,
            display_time=(r.get("an_dt") or "").strip() or None,
            attachment_url=(r.get("attchmntFile") or "").strip() or None,
            industry=(r.get("smIndustry") or "").strip() or None,
            has_xbrl=bool(r.get("hasXbrl") in (True, "true", "1", 1)),
        ))
    # NSE returns newest-first; keep that ordering (sort_date desc as a guard).
    out.sort(key=lambda a: a.broadcast_at or "", reverse=True)
    return out


def _window(days: int) -> list[AnnouncementFeedRow]:
    now = time.time()
    hit = _cache.get(days)
    if hit and now - hit[0] < _CACHE_TTL:
        return hit[1]
    rows = _fetch_window(days)
    if rows:                       # don't cache an empty fetch (likely rate-limited)
        _cache[days] = (now, rows)
    return rows


def feed(
    category: str | None = None,
    symbol: str | None = None,
    q: str | None = None,
    days: int = 2,
    include_routine: bool = False,
    limit: int = 100,
    universe: str | None = None,
) -> list[AnnouncementFeedRow]:
    rows = _window(days)
    from backend.services import universe_service
    rows = universe_service.filter_rows(rows, universe)
    if category:
        rows = [r for r in rows if r.category == category]
    elif not include_routine:
        rows = [r for r in rows if r.category not in _ROUTINE]
    if symbol:
        sym = symbol.upper()
        rows = [r for r in rows if r.symbol == sym]
    if q:
        needle = q.lower()
        rows = [
            r for r in rows
            if needle in (r.name or "").lower()
            or needle in (r.symbol or "").lower()
            or needle in (r.desc or "").lower()
            or needle in (r.detail or "").lower()
        ]
    return rows[:limit]
