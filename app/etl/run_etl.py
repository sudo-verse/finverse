"""ETL orchestrator — initialize the DB and run all loaders in order.

Usage:
    python -m app.etl.run_etl                 # companies + 1mo prices + signals
    python -m app.etl.run_etl --prices 6mo    # longer price history
    python -m app.etl.run_etl --limit 20      # cap companies (quick run)
    python -m app.etl.run_etl --skip-prices   # skip the slow price fetch
"""

import argparse

from app.db.init_db import init_db
from app.etl import companies_etl, prices_etl, signals_etl
from app.utils.logger import logger


def run(price_period="1mo", limit=None, skip_prices=False):
    logger.info("=== ETL pipeline start ===")
    init_db()

    companies_etl.run()

    if skip_prices:
        logger.info("prices_etl: skipped")
    else:
        prices_etl.run(period=price_period, limit=limit)

    signals_etl.run()
    logger.info("=== ETL pipeline complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Finverse ETL pipeline")
    parser.add_argument("--prices", default="1mo", help="yfinance price period (default 1mo)")
    parser.add_argument("--limit", type=int, default=None, help="cap number of companies")
    parser.add_argument("--skip-prices", action="store_true", help="skip price ingestion")
    args = parser.parse_args()

    run(price_period=args.prices, limit=args.limit, skip_prices=args.skip_prices)
