"""Insider (SEBI PIT) and substantial-acquisition (SAST) disclosures.

Market-wide path uses SAST Reg29 (`corporate-sast-reg29`) — it returns the
whole market over a date window. Per-stock insider trades use the per-symbol
`corporates-pit` endpoint (the market-wide PIT aggregation returns empty).
Both go through the warmed NSE session (Mumbai-IP only); the market feed is
cached ~5 min.
"""

import time
from datetime import date, timedelta

from backend.schemas.insider import InsiderTrade, SastRow

_SAST_URL = "https://www.nseindia.com/api/corporate-sast-reg29"
_PIT_URL = "https://www.nseindia.com/api/corporates-pit"
_CACHE_TTL = 300
_sast_cache: dict[int, tuple[float, list[SastRow]]] = {}


def _num(v) -> float | None:
    if v is None:
        return None
    s = str(v).replace(",", "").strip()
    if s in ("", "-", "NA", "null", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _int(v) -> int | None:
    n = _num(v)
    return int(n) if n is not None else None


def _get(url: str, params: dict) -> list:
    from app.market import nse_shp

    for _ in range(2):
        try:
            r = nse_shp._sess().get(url, params=params, timeout=25)
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


def _sast_row(r: dict) -> SastRow:
    action = (r.get("acqSaleType") or "").strip() or None
    is_sale = (action or "").lower().startswith("sale") or (action or "").lower().startswith("dispos")
    shares = _int(r.get("noOfShareSale")) if is_sale else _int(r.get("noOfShareAcq"))
    pct_traded = _num(r.get("totSaleShare")) if is_sale else _num(r.get("totAcqShare"))
    return SastRow(
        symbol=(r.get("symbol") or "").strip().upper() or None,
        company=(r.get("company") or "").strip() or None,
        acquirer=" ".join((r.get("acquirerName") or "").split()) or None,
        action=action,
        is_promoter=(r.get("promoterType") or "").strip().upper() == "Y",
        shares=shares,
        pct_traded=pct_traded,
        pct_after=_num(r.get("totAftShare")),
        mode=(r.get("acquisitionMode") or "").strip() or None,
        reg_type=(r.get("regType") or "").strip() or None,
        trade_date=(r.get("acquirerDate") or "").strip() or None,
        filed_at=(r.get("timestamp") or r.get("sysTime") or "").strip() or None,
        attachment_url=(r.get("attachement") or "").strip() or None,
    )


def _sast_window(days: int) -> list[SastRow]:
    now = time.time()
    hit = _sast_cache.get(days)
    if hit and now - hit[0] < _CACHE_TTL:
        return hit[1]
    to_d = date.today()
    from_d = to_d - timedelta(days=days)
    raw = _get(_SAST_URL, {
        "index": "equities",
        "from_date": from_d.strftime("%d-%m-%Y"),
        "to_date": to_d.strftime("%d-%m-%Y"),
    })
    rows = [_sast_row(r) for r in raw]
    if rows:
        _sast_cache[days] = (now, rows)
    return rows


def sast_feed(
    action: str | None = None,
    symbol: str | None = None,
    promoter_only: bool = False,
    q: str | None = None,
    days: int = 5,
    limit: int = 100,
) -> list[SastRow]:
    rows = _sast_window(days)
    if action:
        a = action.lower()
        rows = [r for r in rows if (r.action or "").lower().startswith(a)]
    if promoter_only:
        rows = [r for r in rows if r.is_promoter]
    if symbol:
        sym = symbol.upper()
        rows = [r for r in rows if r.symbol == sym]
    if q:
        needle = q.lower()
        rows = [
            r for r in rows
            if needle in (r.company or "").lower()
            or needle in (r.symbol or "").lower()
            or needle in (r.acquirer or "").lower()
        ]
    return rows[:limit]


def stock_insider(symbol: str, limit: int = 25) -> list[InsiderTrade]:
    """Per-symbol SEBI PIT insider trades (named insiders, buy/sell)."""
    raw = _get(_PIT_URL, {"index": "equities", "symbol": symbol.upper()})
    out: list[InsiderTrade] = []
    for r in raw[:limit]:
        out.append(InsiderTrade(
            symbol=(r.get("symbol") or "").strip().upper() or None,
            person=" ".join((r.get("acqName") or "").split()) or None,
            person_category=(r.get("personCategory") or "").strip() or None,
            transaction_type=(r.get("tdpTransactionType") or "").strip() or None,
            security_type=(r.get("secType") or "").strip() or None,
            quantity=_int(r.get("secAcq")),
            value=_num(r.get("secVal")),
            pct_before=_num(r.get("befAcqSharesPer")),
            pct_after=_num(r.get("afterAcqSharesPer")),
            mode=(r.get("acqMode") or "").strip() or None,
            trade_date=(r.get("acqfromDt") or "").strip() or None,
            filed_at=(r.get("date") or r.get("intimDt") or "").strip() or None,
        ))
    return out
