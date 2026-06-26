"""IPO / SME-IPO tracker over NSE's primary-market feeds.

  • open      — `ipo-current-issue` (mainboard) + `?index=sme` (SME), with the
                live subscription multiple (noOfTime).
  • upcoming  — `all-upcoming-issues?category=ipo`.
  • listed    — `public-past-issues`, most recently listed first.

All work from the Mumbai box via the warmed NSE session; cached ~30 min,
fail-open (empty on error).
"""

import re
import time
from datetime import datetime

from backend.schemas.ipo import IpoRow

_CUR_URL = "https://www.nseindia.com/api/ipo-current-issue"
_UP_URL = "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
_PAST_URL = "https://www.nseindia.com/api/public-past-issues"
_CACHE_TTL = 1800
_cache: dict[str, tuple[float, list[IpoRow]]] = {}

_PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _band(s: str | None) -> tuple[str | None, float | None, float | None]:
    """'Rs.107 to Rs.113' -> ('₹107–₹113', 107, 113)."""
    if not s or s.strip() in ("-", ""):
        return None, None, None
    nums = [float(x) for x in _PRICE_RE.findall(s)]
    if not nums:
        return s.strip(), None, None
    lo, hi = min(nums), max(nums)
    pretty = f"₹{lo:g}" if lo == hi else f"₹{lo:g}–₹{hi:g}"
    return pretty, lo, hi


def _get(url: str) -> list:
    from app.market import nse_shp

    for _ in range(2):
        try:
            r = nse_shp._sess().get(url, timeout=20)
            if r.status_code == 200:
                d = r.json()
                return d if isinstance(d, list) else (d or {}).get("data", []) or []
            nse_shp._sess().get(nse_shp._HOME, timeout=10)
        except Exception:
            try:
                nse_shp._sess().get(nse_shp._HOME, timeout=10)
            except Exception:
                pass
    return []


def _row_current(r: dict, category: str, status: str) -> IpoRow:
    pretty, lo, hi = _band(r.get("issuePrice"))
    return IpoRow(
        symbol=(r.get("symbol") or "").strip().upper() or None,
        name=(r.get("companyName") or "").strip(),
        category=category, status=status,
        price_band=pretty, price_min=lo, price_max=hi,
        issue_size=(str(r.get("issueSize")).strip() if r.get("issueSize") else None),
        open_date=(r.get("issueStartDate") or "").strip() or None,
        close_date=(r.get("issueEndDate") or "").strip() or None,
        subscription=_num(r.get("noOfTime")),
    )


def _parse_date(s: str | None):
    if not s or s.strip() in ("-", ""):
        return None
    for fmt in ("%d-%b-%Y", "%d-%B-%Y"):
        try:
            return datetime.strptime(s.strip().title(), fmt)
        except ValueError:
            continue
    return None


def _cached(key: str, builder) -> list[IpoRow]:
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < _CACHE_TTL:
        return hit[1]
    rows = builder()
    if rows:
        _cache[key] = (now, rows)
    return rows


def open_issues() -> list[IpoRow]:
    def build():
        out: list[IpoRow] = []
        seen = set()
        for cat, url in (("Mainboard", _CUR_URL), ("SME", f"{_CUR_URL}?index=sme")):
            for r in _get(url):
                row = _row_current(r, cat, "open")
                key = (row.symbol, row.name)
                if key in seen:
                    continue
                seen.add(key)
                out.append(row)
        return out
    return _cached("open", build)


def upcoming_issues() -> list[IpoRow]:
    def build():
        return [_row_current(r, "Mainboard", "upcoming") for r in _get(_UP_URL)]
    return _cached("upcoming", build)


def listed_issues(limit: int = 40) -> list[IpoRow]:
    def build():
        rows = []
        for r in _get(_PAST_URL):
            ld = _parse_date(r.get("listingDate"))
            if ld is None:
                continue
            sym = (r.get("symbol") or "").strip().upper()
            # skip debt/bond listings (NCDs etc.) — their symbols are numeric-prefixed
            if not sym or sym[0].isdigit():
                continue
            pretty, lo, hi = _band(r.get("priceRange") or r.get("issuePrice"))
            rows.append((ld, IpoRow(
                symbol=(r.get("symbol") or "").strip().upper() or None,
                name=(r.get("company") or "").strip(),
                category="Mainboard", status="listed",
                price_band=pretty, price_min=lo, price_max=hi,
                open_date=(r.get("ipoStartDate") or "").strip() or None,
                close_date=(r.get("ipoEndDate") or "").strip() or None,
                listing_date=(r.get("listingDate") or "").strip() or None,
            )))
        rows.sort(key=lambda t: t[0], reverse=True)
        return [r for _, r in rows]
    return _cached("listed", build)[:limit]


def feed(status: str = "open", limit: int = 40) -> list[IpoRow]:
    if status == "upcoming":
        return upcoming_issues()[:limit]
    if status == "listed":
        return listed_issues(limit)
    return open_issues()[:limit]
