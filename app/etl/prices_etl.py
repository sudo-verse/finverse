"""ETL: fetch historical OHLCV from Yahoo Finance into `price_history`."""

import yfinance as yf

from app.db.database import get_session
from app.db.models import Company
from app.db.repository import upsert_price
from app.utils.logger import logger


def _load_symbols(limit=None, symbols=None):
    with get_session() as session:
        q = session.query(Company.id, Company.symbol).order_by(Company.id)
        if symbols:
            q = q.filter(Company.symbol.in_(symbols))
        if limit:
            q = q.limit(limit)
        return list(q.all())


def run(period="1mo", limit=None, symbols=None):
    """Load `period` of daily bars for each company.

    period  : yfinance period string ("1mo", "6mo", "1y", "max", ...)
    limit   : cap the number of companies (handy for quick runs/tests)
    symbols : restrict to a specific list of symbols (e.g. a peer group)
    """
    companies = _load_symbols(limit=limit, symbols=symbols)
    logger.info(f"prices_etl: fetching {period} OHLCV for {len(companies)} companies")

    total_rows = 0
    for company_id, symbol in companies:
        try:
            df = yf.Ticker(f"{symbol}.NS").history(period=period, auto_adjust=False)
            if df.empty:
                continue

            with get_session() as session:
                for ts, r in df.iterrows():
                    upsert_price(
                        session,
                        company_id=company_id,
                        date=ts.date(),
                        open_=float(r["Open"]),
                        high=float(r["High"]),
                        low=float(r["Low"]),
                        close=float(r["Close"]),
                        volume=int(r["Volume"]),
                    )
                    total_rows += 1

        except Exception as e:
            logger.error(f"prices_etl: {symbol} failed: {e}")

    logger.info(f"prices_etl: upserted {total_rows} price rows")
    return total_rows


if __name__ == "__main__":
    run()
