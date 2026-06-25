"""Sector-performance heatmap from NSE's allIndices feed.

Filters the full index list down to the sectoral indices and exposes their
day / week / month / year change. Live data (no DB) with a short in-memory
cache so a busy dashboard doesn't hammer NSE. Indian-IP only.
"""

import time

from backend.schemas.sectors import SectorPerf

_URL = "https://www.nseindia.com/api/allIndices"
_CACHE_TTL = 60
_cache: tuple[float, list[SectorPerf]] | None = None

# NSE index name → short display label. Curated so the heatmap shows the
# recognised sectors (not the 130+ broad/strategy/thematic indices).
_SECTORS = {
    "NIFTY BANK": "Bank",
    "NIFTY PRIVATE BANK": "Pvt Bank",
    "NIFTY PSU BANK": "PSU Bank",
    "NIFTY FINANCIAL SERVICES": "Financials",
    "NIFTY IT": "IT",
    "NIFTY AUTO": "Auto",
    "NIFTY PHARMA": "Pharma",
    "NIFTY HEALTHCARE INDEX": "Healthcare",
    "NIFTY FMCG": "FMCG",
    "NIFTY METAL": "Metal",
    "NIFTY REALTY": "Realty",
    "NIFTY MEDIA": "Media",
    "NIFTY ENERGY": "Energy",
    "NIFTY OIL & GAS": "Oil & Gas",
    "NIFTY CONSUMER DURABLES": "Consumer Dur",
    "NIFTY INFRASTRUCTURE": "Infra",
}


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _fetch() -> list[dict]:
    from app.market import nse_shp

    for attempt in (1, 2):
        try:
            r = nse_shp._sess().get(_URL, timeout=15)
            if r.status_code == 200:
                return (r.json() or {}).get("data") or []
            if attempt == 1:
                nse_shp._sess().get(nse_shp._HOME, timeout=10)
        except Exception:
            if attempt == 1:
                try:
                    nse_shp._sess().get(nse_shp._HOME, timeout=10)
                except Exception:
                    pass
    return []


class SectorService:
    def heatmap(self) -> list[SectorPerf]:
        global _cache
        if _cache and time.time() - _cache[0] < _CACHE_TTL:
            return _cache[1]

        out: list[SectorPerf] = []
        for row in _fetch():
            label = _SECTORS.get((row.get("index") or "").strip().upper())
            if not label:
                continue
            last = _num(row.get("last"))
            week_ago = _num(row.get("oneWeekAgoVal"))
            week = round((last - week_ago) / week_ago * 100, 2) if (last and week_ago) else None
            out.append(SectorPerf(
                name=label, index=row.get("index"), last=last,
                day=_num(row.get("percentChange")), week=week,
                month=_num(row.get("perChange30d")), year=_num(row.get("perChange365d")),
                advances=int(_num(row.get("advances")) or 0) or None,
                declines=int(_num(row.get("declines")) or 0) or None,
                pe=_num(row.get("pe")),
            ))
        out.sort(key=lambda s: (s.day if s.day is not None else -999), reverse=True)
        if out:
            _cache = (time.time(), out)
        return out


sector_service = SectorService()
