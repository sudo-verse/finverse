"""Marquee-investor ("superstar") tracker.

India's well-known investors and notable funds, matched by name against the
disclosed bulk/block-deal book (`deals` table) and SAST acquirers. Aggregates
each investor's recent buys/sells and the stocks they touched.

Honest scope: bulk/block deals capture only large *disclosed* trades, so this is
sparse until those investors transact — but it never mislabels an HFT/prop desk
as a superstar (only curated names match). Grows as the daily deal ETL runs.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.models import Deal
from backend.schemas.superstar import SuperstarRow, SuperstarTrade

# (canonical name, kind, [uppercase match substrings])
_INVESTORS: list[tuple[str, str, list[str]]] = [
    ("Rakesh / Rekha Jhunjhunwala", "Investor", ["JHUNJHUNWALA", "RARE ENTERPRISES"]),
    ("Radhakishan Damani", "Investor", ["RADHAKISHAN DAMANI", "RADHA KISHAN DAMANI", "DERIVE TRADING", "BRIGHT STAR INVESTMENT"]),
    ("Ashish Kacholia", "Investor", ["ASHISH KACHOLIA", "BENGAL FINANCE"]),
    ("Mukul Agrawal", "Investor", ["MUKUL AGRAWAL", "MUKUL MAHAVIR"]),
    ("Vijay Kedia", "Investor", ["VIJAY KEDIA", "KEDIA SECURITIES"]),
    ("Dolly / Rajiv Khanna", "Investor", ["DOLLY KHANNA", "RAJIV KHANNA"]),
    ("Ashish Dhawan", "Investor", ["ASHISH DHAWAN"]),
    ("Porinju Veliyath", "Investor", ["PORINJU", "EQUITY INTELLIGENCE"]),
    ("Sunil Singhania (Abakkus)", "Fund", ["SINGHANIA", "ABAKKUS"]),
    ("Madhusudan Kela", "Investor", ["MADHUSUDAN KELA", "MK VENTURES"]),
    ("Anil Kumar Goel", "Investor", ["ANIL KUMAR GOEL", "ANIL GOEL"]),
    ("Nemish Shah", "Investor", ["NEMISH SHAH"]),
    ("Hitesh Doshi", "Investor", ["HITESH RAMJI DOSHI", "HITESH DOSHI"]),
    ("Akash Bhanshali", "Investor", ["AKASH BHANSHALI"]),
    ("Ramesh Damani", "Investor", ["RAMESH DAMANI"]),
    ("Malabar", "Fund", ["MALABAR"]),
    ("Nalanda", "Fund", ["NALANDA"]),
    ("SmallCap World Fund", "Fund", ["SMALLCAP WORLD"]),
    ("Norges (Govt Pension Fund)", "Fund", ["NORGES", "GOVERNMENT PENSION FUND GLOBAL"]),
    ("Fidelity", "Fund", ["FIDELITY", "FID FUNDS"]),
    ("Vanguard", "Fund", ["VANGUARD"]),
    ("Government of Singapore", "Fund", ["GOVERNMENT OF SINGAPORE", "MONETARY AUTHORITY OF SINGAPORE"]),
    ("Abu Dhabi Investment Authority", "Fund", ["ABU DHABI INVESTMENT"]),
    ("Quant Mutual Fund", "Fund", ["QUANT MUTUAL", "QUANT MONEY MANAGERS"]),
    ("Tata Mutual Fund", "Fund", ["TATA MUTUAL", "TATA ABSOLUTE"]),
]


def _match(name: str | None) -> tuple[str, str] | None:
    if not name:
        return None
    up = name.upper()
    for canon, kind, pats in _INVESTORS:
        if any(p in up for p in pats):
            return canon, kind
    return None


def leaderboard(session: Session, days: int = 365, limit: int = 30) -> list[SuperstarRow]:
    cutoff = date.today() - timedelta(days=days)
    deals = (
        session.query(Deal)
        .filter(Deal.deal_date >= cutoff)
        .order_by(Deal.deal_date.desc())
        .all()
    )

    groups: dict[str, dict] = {}
    for d in deals:
        m = _match(d.client_name)
        if not m:
            continue
        canon, kind = m
        g = groups.setdefault(canon, {"kind": kind, "trades": [], "buy": 0.0, "sell": 0.0,
                                      "stocks": set(), "last": None})
        g["trades"].append(SuperstarTrade(
            symbol=d.symbol, name=d.name, side=d.side, value=d.value,
            deal_date=d.deal_date, deal_type=d.deal_type,
        ))
        if d.symbol:
            g["stocks"].add(d.symbol)
        v = d.value or 0.0
        if (d.side or "").upper() == "SELL":
            g["sell"] += v
        else:
            g["buy"] += v
        if g["last"] is None or d.deal_date > g["last"]:
            g["last"] = d.deal_date

    rows = [
        SuperstarRow(
            investor=canon, kind=g["kind"], num_trades=len(g["trades"]),
            buy_value=round(g["buy"], 2), sell_value=round(g["sell"], 2),
            last_active=g["last"], stocks=sorted(g["stocks"]),
            trades=g["trades"][:12],
        )
        for canon, g in groups.items()
    ]
    rows.sort(key=lambda r: (r.last_active or date.min, r.num_trades), reverse=True)
    return rows[:limit]
