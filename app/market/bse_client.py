"""Backup market-data provider: BSE (Bombay Stock Exchange) official API.

Last-resort live-price fallback used when the primary NSE index feed and the
Yahoo Finance fallback both fail. Indian equities are dual-listed on NSE and
BSE, so BSE provides a price source independent of both NSE and Yahoo. It is
free and needs no API key — but, like NSE, BSE only serves Indian IPs, so this
only works when the app runs from India (the prod box is in ap-south-1/Mumbai).

BSE quotes by numeric scrip code, so prices are resolved in two hops:
    NSE symbol -> ISIN (from the bundled nse_equity_list.csv)
              -> BSE scrip code (from BSE's scrip master, cached on disk).
Both maps are built lazily on first use; the scrip master is refreshed weekly.
"""

import csv
import json
import os
import time

import requests

from app.config import CHROMA_DIR
from app.utils.logger import logger

_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.bseindia.com/",
    "Accept": "application/json",
}
_SCRIP_LIST_URL = "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w"
_QUOTE_URL = "https://api.bseindia.com/BseIndiaAPI/api/getScripHeaderData/w"
_CACHE_TTL = 7 * 24 * 3600  # refresh the BSE scrip master weekly

_session = requests.Session()
_symbol_to_isin: dict | None = None
_isin_to_code: dict | None = None


def is_configured() -> bool:
    return True  # no API key required


def _load_symbol_isin() -> dict:
    """NSE symbol -> ISIN, from the bundled equity universe CSV."""
    global _symbol_to_isin
    if _symbol_to_isin is None:
        m: dict[str, str] = {}
        try:
            with open("nse_equity_list.csv", newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    sym = (row.get("Symbol") or "").strip().upper()
                    isin = (row.get("ISIN Code") or "").strip().upper()
                    if sym and isin:
                        m[sym] = isin
        except Exception as e:
            logger.warning("bse: failed to load symbol->isin map: %s", e)
        _symbol_to_isin = m
    return _symbol_to_isin


def _fetch_scrip_master() -> dict:
    """ISIN -> BSE scrip code, from BSE's active-equity scrip master."""
    params = {"Group": "", "Scripcode": "", "industry": "",
              "segment": "Equity", "status": "Active"}
    res = _session.get(_SCRIP_LIST_URL, params=params, headers=_HEADERS, timeout=30)
    res.raise_for_status()
    out: dict[str, str] = {}
    for row in res.json():
        isin = (row.get("ISIN_NUMBER") or "").strip().upper()
        code = str(row.get("SCRIP_CD") or "").strip()
        if isin and code:
            out[isin] = code
    return out


def _load_scrip_map() -> dict:
    """ISIN -> BSE scrip code, cached on disk under CHROMA_DIR (weekly refresh)."""
    global _isin_to_code
    if _isin_to_code is not None:
        return _isin_to_code

    cache_path = os.path.join(CHROMA_DIR, "bse_scrip_map.json")
    try:
        if os.path.exists(cache_path) and time.time() - os.path.getmtime(cache_path) < _CACHE_TTL:
            with open(cache_path, encoding="utf-8") as f:
                _isin_to_code = json.load(f)
                return _isin_to_code
    except Exception as e:
        logger.warning("bse: scrip cache read failed: %s", e)

    try:
        _isin_to_code = _fetch_scrip_master()
        logger.info("bse: loaded %d scrip codes", len(_isin_to_code))
        try:
            os.makedirs(CHROMA_DIR, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(_isin_to_code, f)
        except Exception as e:
            logger.warning("bse: scrip cache write failed: %s", e)
    except Exception as e:
        logger.warning("bse: failed to fetch scrip master: %s", e)
        _isin_to_code = _isin_to_code or {}
    return _isin_to_code


def _scrip_code(symbol: str) -> str | None:
    isin = _load_symbol_isin().get(symbol.upper())
    return _load_scrip_map().get(isin) if isin else None


def get_price(symbol: str) -> float | None:
    """Latest BSE price for an NSE symbol (dual-listed), or None on any failure."""
    code = _scrip_code(symbol)
    if not code:
        return None
    try:
        res = _session.get(
            _QUOTE_URL,
            params={"Debtflag": "", "scripcode": code, "seriesid": ""},
            headers=_HEADERS, timeout=10,
        )
        if res.status_code == 200:
            ltp = (res.json().get("CurrRate") or {}).get("LTP")
            if ltp not in (None, "", "0", "0.00"):
                return float(str(ltp).replace(",", ""))
        else:
            logger.warning("bse: %s (code %s) -> HTTP %s", symbol, code, res.status_code)
    except Exception as e:  # network / parse — fall through to None
        logger.warning("bse: %s (code %s) failed: %s", symbol, code, e)
    return None
