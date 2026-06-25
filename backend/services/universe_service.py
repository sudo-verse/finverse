"""Stock-universe filtering by NSE index membership (Nifty 50/100/200/500).

Membership comes from NSE's official published constituent CSVs (the
`equity-stockIndices` JSON API is blocked, but the archive CSVs work). Lists are
fetched lazily through the warmed NSE session and cached for a day. The filter
is **fail-open**: if a list can't be fetched, `members()` returns None and the
caller shows the full universe rather than an empty page.
"""

import csv
import io
import time

_BASE = "https://nsearchives.nseindia.com/content/indices/"
_FILES = {
    "nifty50": "ind_nifty50list.csv",
    "nifty100": "ind_nifty100list.csv",
    "nifty200": "ind_nifty200list.csv",
    "nifty500": "ind_nifty500list.csv",
}

# Ordered options for the UI (key, label). "all" = no filter.
UNIVERSES = [
    {"key": "all", "label": "All stocks"},
    {"key": "nifty50", "label": "Nifty 50"},
    {"key": "nifty100", "label": "Nifty 100"},
    {"key": "nifty200", "label": "Nifty 200"},
    {"key": "nifty500", "label": "Nifty 500"},
]

_CACHE_TTL = 86_400  # a day; constituents change only at quarterly reviews
_cache: dict[str, tuple[float, set[str]]] = {}


def _fetch(key: str) -> set[str] | None:
    from app.market import nse_shp

    fname = _FILES.get(key)
    if not fname:
        return None
    try:
        r = nse_shp._sess().get(_BASE + fname, timeout=20)
        if r.status_code != 200:
            return None
        syms = {
            (row.get("Symbol") or "").strip().upper()
            for row in csv.DictReader(io.StringIO(r.text))
        }
        syms.discard("")
        return syms or None
    except Exception:
        return None


def members(key: str | None) -> set[str] | None:
    """Uppercase symbols in the index, or None for 'all' / unknown / fetch
    failure (fail-open — the caller then applies no filter)."""
    key = (key or "all").lower()
    if key == "all" or key not in _FILES:
        return None

    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < _CACHE_TTL:
        return hit[1]

    fetched = _fetch(key)
    if fetched:
        _cache[key] = (now, fetched)
        return fetched
    return hit[1] if hit else None  # serve stale if we have it, else fail-open


def filter_rows(rows: list, key: str | None) -> list:
    """Keep only rows whose `.symbol` is in the chosen index (no-op for 'all')."""
    allowed = members(key)
    if allowed is None:
        return rows
    return [r for r in rows if (getattr(r, "symbol", "") or "").upper() in allowed]
