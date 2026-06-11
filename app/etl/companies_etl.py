"""ETL: load the NSE company master from CSV into the `companies` table."""

import pandas as pd

from app.db.database import get_session
from app.db.repository import upsert_company
from app.utils.logger import logger

CSV_PATH = "ind_nifty500list.csv"


def run(csv_path=CSV_PATH):
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"companies_etl: failed to read {csv_path}: {e}")
        return 0

    count = 0
    with get_session() as session:
        for _, row in df.iterrows():
            symbol = str(row.get("Symbol", "")).strip()
            if not symbol:
                continue

            upsert_company(
                session,
                symbol=symbol,
                name=str(row.get("Company Name", "")).strip(),
                industry=str(row.get("Industry", "")).strip() or None,
                isin=str(row.get("ISIN Code", "")).strip() or None,
                series=str(row.get("Series", "")).strip() or None,
            )
            count += 1

    logger.info(f"companies_etl: upserted {count} companies")
    return count


if __name__ == "__main__":
    run()
