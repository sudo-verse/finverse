"""NSE surveillance flags — ASM (Additional Surveillance Measure) and GSM
(Graded Surveillance Measure) lists.

Both are market-wide JSON lists from NSE (work from the Mumbai box via the
warmed session). A stock on ASM/GSM is under extra surveillance for unusual
price/volume or weak fundamentals — a clear red flag. Cached ~30 min; fail-open
(empty on error) so a flaky NSE never breaks the stock page.
"""

import time

_ASM_URL = "https://www.nseindia.com/api/reportASM"
_GSM_URL = "https://www.nseindia.com/api/reportGSM"
_CACHE_TTL = 1800
_cache: tuple[float, dict] | None = None


def _fetch() -> dict:
    """symbol -> {'asm': str|None, 'gsm': str|None, 'desc': str|None}."""
    from app.market import nse_shp

    sess = nse_shp._sess()
    out: dict[str, dict] = {}
    try:
        asm = sess.get(_ASM_URL, timeout=20).json()
        for term, key in (("Long-term", "longterm"), ("Short-term", "shortterm")):
            for r in (asm.get(key) or {}).get("data", []) or []:
                sym = (r.get("symbol") or "").strip().upper()
                if not sym:
                    continue
                out.setdefault(sym, {})["asm"] = f"{r.get('asmSurvIndicator') or 'ASM'} ({term})"
                out[sym]["desc"] = (r.get("survDesc") or "").strip() or out[sym].get("desc")
    except Exception:
        pass
    try:
        gsm = sess.get(_GSM_URL, timeout=20).json()
        for r in gsm if isinstance(gsm, list) else []:
            sym = (r.get("symbol") or "").strip().upper()
            if not sym:
                continue
            out.setdefault(sym, {})["gsm"] = f"Stage {r.get('gsmStage') or '?'}"
            out[sym]["desc"] = (r.get("survDesc") or "").strip() or out[sym].get("desc")
            out[sym]["name"] = (r.get("companyName") or "").strip()
    except Exception:
        pass
    return out


def _all() -> dict:
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < _CACHE_TTL:
        return _cache[1]
    data = _fetch()
    if data:                      # don't cache an empty (failed) fetch for long
        _cache = (now, data)
    else:
        _cache = (now - _CACHE_TTL + 120, {})   # retry in ~2 min
    return data


def flags(symbol: str) -> dict | None:
    return _all().get(symbol.upper())


def feed() -> list[dict]:
    """Flat list of surveilled stocks for a market view."""
    rows = []
    for sym, d in _all().items():
        rows.append({
            "symbol": sym,
            "name": d.get("name"),
            "asm": d.get("asm"),
            "gsm": d.get("gsm"),
            "desc": d.get("desc"),
        })
    rows.sort(key=lambda r: (r["gsm"] is None, r["symbol"]))   # GSM (more severe) first
    return rows
