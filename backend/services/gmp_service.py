"""Grey-market premium (GMP) for IPOs.

GMP is unofficial grey-market data — not on NSE. We scrape the public GMP table
at ipowatch.in (server-rendered HTML), parse per-IPO GMP / estimated listing /
estimated gain, and match it to our NSE IPO rows by normalised company name.
Cached ~30 min, fail-open (no GMP shown on error).
"""

import re
import time

_URL = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
_CACHE_TTL = 1800
_cache: tuple[float, dict] | None = None

_STRIP = re.compile(r"<[^>]+>")
_SUFFIX = re.compile(r"\b(limited|ltd|ipo|pvt|private)\b\.?", re.I)


def _norm(name: str) -> str:
    s = _SUFFIX.sub("", (name or "").lower())
    return re.sub(r"[^a-z0-9]", "", s)


def _money(s: str | None) -> float | None:
    if not s:
        return None
    m = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", s)
    return float(m.group(1).replace(",", "")) if m else None


def _pct(s: str | None) -> float | None:
    if not s:
        return None
    m = re.search(r"\(?\s*([-\d.]+)\s*%", s)
    return float(m.group(1)) if m else None


def _fetch() -> dict:
    import requests

    out: dict[str, dict] = {}
    try:
        r = requests.get(_URL, headers={"User-Agent": _UA}, timeout=25)
        if r.status_code != 200:
            return out
        html = r.text
    except Exception:
        return out

    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        cells = [_STRIP.sub("", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) < 5 or "₹" not in cells[1]:
            continue
        name = cells[0]
        gmp = _money(cells[1])
        # estimated-listing cell holds "₹183 (7.65%)"
        est_cell = next((c for c in cells[3:6] if "(" in c and "%" in c), cells[4] if len(cells) > 4 else None)
        out[_norm(name)] = {
            "gmp": gmp,
            "est_listing": _money(est_cell),
            "gmp_pct": _pct(est_cell),
            "name": name,
        }
    return out


def _all() -> dict:
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < _CACHE_TTL:
        return _cache[1]
    data = _fetch()
    if data:
        _cache = (now, data)
    else:
        _cache = (now - _CACHE_TTL + 120, {})   # retry in ~2 min on failure
    return data


def for_company(name: str | None) -> dict | None:
    if not name:
        return None
    return _all().get(_norm(name))
