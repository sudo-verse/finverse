"""F&O / derivatives analytics from the NSE EOD FO bhavcopy (UDiFF).

NSE's live option-chain API is blocked from servers, but the daily FO bhavcopy
zip (settlement OI/volume for every futures & options contract) is downloadable
from the archive. We parse the latest available day once and derive, per
underlying: futures OI + OI-change buildup, put/call ratio and max pain, plus a
per-symbol option chain (nearest expiry). EOD data, cached for the day.
"""

import csv
import io
import logging
import time
import zipfile
from collections import defaultdict
from datetime import date, timedelta

from backend.schemas.derivatives import DerivativeRow, OptionChainOut, OptionStrike

logger = logging.getLogger("finverse.api")

_URL = "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{ymd}_F_0000.csv.zip"
_CACHE_TTL = 6 * 3600
_cache: tuple[float, dict] | None = None


def _num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def _fetch_rows():
    """(as_of_str, csv rows) for the most recent available trading day."""
    from app.market import nse_shp

    for back in range(0, 6):
        d = date.today() - timedelta(days=back)
        try:
            r = nse_shp._sess().get(_URL.format(ymd=d.strftime("%Y%m%d")), timeout=35)
            if r.status_code == 200 and r.content:
                z = zipfile.ZipFile(io.BytesIO(r.content))
                text = z.read(z.namelist()[0]).decode("utf-8", "ignore").splitlines()
                return d.isoformat(), csv.DictReader(text)
        except Exception:
            continue
    return None, None


def _buildup(price_chg: float | None, oi_chg: float | None) -> str | None:
    if price_chg is None or oi_chg is None or oi_chg == 0:
        return None
    if oi_chg > 0:
        return "Long buildup" if price_chg >= 0 else "Short buildup"
    return "Short covering" if price_chg >= 0 else "Long unwinding"


def _max_pain(strikes: dict) -> float | None:
    """Strike that minimises total in-the-money option payout at expiry."""
    if not strikes:
        return None
    ks = sorted(strikes)
    best_k, best_pain = None, None
    for e in ks:                       # candidate expiry prices = listed strikes
        pain = 0.0
        for k, oi in strikes.items():
            if e > k:
                pain += (e - k) * oi.get("CE", 0.0)   # CE writers pay when price>strike
            elif e < k:
                pain += (k - e) * oi.get("PE", 0.0)   # PE writers pay when price<strike
        if best_pain is None or pain < best_pain:
            best_pain, best_k = pain, e
    return best_k


def _build() -> dict:
    as_of, rows = _fetch_rows()
    if rows is None:
        return {"as_of": None, "summary": [], "chains": {}}

    futures: dict[str, dict] = {}
    # sym -> expiry -> strike -> {CE, PE}
    opts: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"CE": 0.0, "PE": 0.0})))

    for r in rows:
        tp = r.get("FinInstrmTp")
        sym = (r.get("TckrSymb") or "").strip().upper()
        if not sym:
            continue
        if tp in ("STF", "IDF"):
            cls = _num(r.get("ClsPric")) or _num(r.get("SttlmPric"))
            prev = _num(r.get("PrvsClsgPric"))
            # nearest-expiry future = smallest XpryDt; keep the first/nearest
            exp = (r.get("XpryDt") or "").strip()
            cur = futures.get(sym)
            if cur is None or (exp and exp < cur.get("expiry", "9999")):
                futures[sym] = {
                    "kind": "Index" if tp == "IDF" else "Stock",
                    "expiry": exp, "close": cls, "prev": prev,
                    "underlying": _num(r.get("UndrlygPric")),
                    "oi": _num(r.get("OpnIntrst")), "chg_oi": _num(r.get("ChngInOpnIntrst")),
                }
        elif tp in ("STO", "IDO"):
            strike = _num(r.get("StrkPric"))
            ot = (r.get("OptnTp") or "").strip().upper()
            exp = (r.get("XpryDt") or "").strip()
            oi = _num(r.get("OpnIntrst")) or 0.0
            if strike is None or ot not in ("CE", "PE"):
                continue
            opts[sym][exp][strike][ot] += oi

    summary: list[DerivativeRow] = []
    chains: dict[str, OptionChainOut] = {}
    for sym, fut in futures.items():
        sym_exps = opts.get(sym, {})
        nearest = min(sym_exps) if sym_exps else None
        strikes = sym_exps.get(nearest, {}) if nearest else {}
        ce = sum(s["CE"] for s in strikes.values())
        pe = sum(s["PE"] for s in strikes.values())
        pcr = round(pe / ce, 2) if ce else None
        mp = _max_pain(strikes)
        chg_pct = (round(fut["chg_oi"] / (fut["oi"] - fut["chg_oi"]) * 100, 1)
                   if fut.get("oi") and fut.get("chg_oi") is not None and (fut["oi"] - fut["chg_oi"]) else None)
        price_chg = (fut["close"] - fut["prev"]) if (fut.get("close") is not None and fut.get("prev") is not None) else None
        summary.append(DerivativeRow(
            symbol=sym, kind=fut["kind"], expiry=fut.get("expiry"),
            fut_price=fut.get("close"), underlying=fut.get("underlying"),
            oi=fut.get("oi"), chg_oi_pct=chg_pct, pcr=pcr, max_pain=mp,
            buildup=_buildup(price_chg, fut.get("chg_oi")),
        ))
        if strikes:
            chains[sym] = OptionChainOut(
                symbol=sym, expiry=nearest, underlying=fut.get("underlying"),
                pcr=pcr, max_pain=mp, as_of=as_of,
                strikes=[OptionStrike(strike=k, ce_oi=v["CE"], pe_oi=v["PE"])
                         for k, v in sorted(strikes.items())],
            )
    return {"as_of": as_of, "summary": summary, "chains": chains}


def _all() -> dict:
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < _CACHE_TTL:
        return _cache[1]
    data = _build()
    if data["summary"]:
        _cache = (now, data)
    return data


def summary(sort: str = "oi", kind: str | None = None, limit: int = 80) -> list[DerivativeRow]:
    rows = list(_all()["summary"])
    if kind:
        rows = [r for r in rows if r.kind.lower() == kind.lower()]
    keyfn = {
        "oi": lambda r: r.oi or 0,
        "pcr": lambda r: r.pcr or 0,
        "chg_oi": lambda r: r.chg_oi_pct or 0,
    }.get(sort, lambda r: r.oi or 0)
    rows.sort(key=keyfn, reverse=True)
    return rows[:limit]


def option_chain(symbol: str, window: int = 12) -> OptionChainOut | None:
    chain = _all()["chains"].get(symbol.upper())
    if chain is None:
        return None
    # trim to the `window` strikes nearest the underlying for a readable chain
    u = chain.underlying
    if u and len(chain.strikes) > window * 2:
        nearest = sorted(chain.strikes, key=lambda s: abs(s.strike - u))[: window * 2]
        chain = chain.model_copy(update={"strikes": sorted(nearest, key=lambda s: s.strike)})
    return chain
