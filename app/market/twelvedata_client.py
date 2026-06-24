"""Backup market-data provider: Twelve Data.

Last-resort live-price fallback used when the primary NSE index feed and the
Yahoo Finance fallback both fail to return a price. Twelve Data's free tier
(~800 requests/day, 8/minute) covers NSE equities, quoted by plain symbol with
``exchange=NSE`` — matching the plain NSE symbols used across the app.

No-op (returns None) when ``TWELVEDATA_API_KEY`` is unset, so the dependency is
fully optional. Get a free key at https://twelvedata.com/.
"""

import requests

from app.config import TWELVEDATA_API_KEY
from app.utils.logger import logger

_BASE_URL = "https://api.twelvedata.com"
_session = requests.Session()


def is_configured() -> bool:
    return bool(TWELVEDATA_API_KEY)


def get_price(symbol: str) -> float | None:
    """Latest price for an NSE symbol via Twelve Data, or None on any failure.

    Twelve Data returns {"price": "1313.60000"} on success and an error object
    ({"status": "error", "message": ...}) on failure (bad symbol, quota, etc.).
    """
    if not TWELVEDATA_API_KEY:
        return None
    try:
        res = _session.get(
            f"{_BASE_URL}/price",
            params={"symbol": symbol, "exchange": "NSE", "apikey": TWELVEDATA_API_KEY},
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            price = data.get("price")
            if price is not None:
                return float(price)
            logger.warning("twelvedata: %s -> %s", symbol, data.get("message", data))
        else:
            logger.warning("twelvedata: %s -> HTTP %s", symbol, res.status_code)
    except Exception as e:  # network / parse / quota — fall through to None
        logger.warning("twelvedata: %s failed: %s", symbol, e)
    return None
