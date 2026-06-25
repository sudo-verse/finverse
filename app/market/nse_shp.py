"""NSE detailed shareholding (FII / DII) via the quarterly XBRL filing.

NSE's summary API gives only Promoter/Public; the FII (Foreign Institutions /
FPI) and DII (Domestic Institutions) split lives in the SEBI-format XBRL filing
linked from `corporate-share-holdings-master`. This module fetches that master
(per-quarter records + promoter/public + an `xbrl` URL), then downloads and
parses each XBRL for the Foreign- and Domestic-institution aggregate holding %.

XBRL stores holdings as fractions (0.5 = 50%), so values are ×100 to percent.
Indian-IP only (NSE blocks foreign IPs) — runs from the Mumbai box.
"""

import time
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

from app.utils.logger import logger

_HOME = "https://www.nseindia.com/"
_MASTER = "https://www.nseindia.com/api/corporate-share-holdings-master"
_HDR = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": _HOME}
_XBRLI = "{http://www.xbrl.org/2003/instance}"
_XBRLDI = "{http://xbrl.org/2006/xbrldi}"
_PCT_TAG = "ShareholdingAsAPercentageOfTotalNumberOfShares"

# SEBI XBRL aggregate dimension members → our columns. The two top-level
# institution buckets, plus the DII sub-categories that answer "who's buying".
_MEMBERS = {
    "fii": "InstitutionsForeignMember",
    "dii": "InstitutionsDomesticMember",
    "mf": "MutualFundsOrUTIMember",
    "insurance": "InsuranceCompaniesMember",
    "banks": "BanksMember",
    "pension": "ProvidentFundsOrPensionFundsMember",
}

_session: requests.Session | None = None


def _sess() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update(_HDR)
        try:
            s.get(_HOME, timeout=10)  # cookie handshake NSE requires
        except Exception:
            pass
        _session = s
    return _session


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_date(s: str):
    try:
        return datetime.strptime((s or "").title(), "%d-%b-%Y").date()
    except Exception:
        return None


def _master(symbol: str):
    for attempt in (1, 2):
        try:
            r = _sess().get(_MASTER, params={"index": "equities", "symbol": symbol}, timeout=15)
            if r.status_code == 200:
                return r.json()
            if attempt == 1:
                _sess().get(_HOME, timeout=10)  # refresh stale cookies
        except Exception as e:
            logger.debug("nse_shp: master %s failed: %s", symbol, e)
            if attempt == 1:
                try:
                    _sess().get(_HOME, timeout=10)
                except Exception:
                    pass
    return []


def _pct_for(root, ctx: dict, member: str):
    """Aggregate holding % for a category member (smallest-dimension context)."""
    out = []
    for el in root.iter():
        if el.tag.endswith("}" + _PCT_TAG):
            cid = el.get("contextRef")
            if cid and member in ctx.get(cid, ()):
                try:
                    out.append((len(ctx[cid]), float(el.text)))
                except (TypeError, ValueError):
                    pass
    return round(sorted(out)[0][1] * 100, 2) if out else None  # fraction → %


def _parse_xbrl(url: str) -> dict:
    try:
        r = _sess().get(url, timeout=25)
        if r.status_code != 200:
            return {}
        root = ET.fromstring(r.content)
        ctx = {}
        for c in root.iter(_XBRLI + "context"):
            ctx[c.get("id")] = {
                (m.text or "").split(":")[-1] for m in c.iter(_XBRLDI + "explicitMember")
            }
        return {k: _pct_for(root, ctx, mem) for k, mem in _MEMBERS.items()}
    except Exception as e:
        logger.debug("nse_shp: xbrl %s failed: %s", url, e)
        return {}


def detail(symbol: str, periods: int = 8, sleep: float = 0.3) -> list[dict]:
    """Latest `periods` quarters, newest first:
    {period_date, period, promoter, public, fii, dii, mf, insurance, banks, pension}.

    NSE's master can list the same quarter twice (a revised + original filing);
    we keep the first (latest revision) per quarter and dedupe the rest."""
    out = []
    seen = set()
    for rec in (_master(symbol) or []):
        if len(out) >= periods:
            break
        pd = _parse_date(rec.get("date", ""))
        if not pd or pd in seen:
            continue
        seen.add(pd)
        row = {
            "period_date": pd, "period": rec.get("date"),
            "promoter": _num(rec.get("pr_and_prgrp")), "public": _num(rec.get("public_val")),
            **{k: None for k in _MEMBERS},  # fii, dii, mf, insurance, banks, pension
        }
        xbrl = rec.get("xbrl")
        if xbrl:
            row.update(_parse_xbrl(xbrl))
            time.sleep(sleep)
        out.append(row)
    return out
