"""ETL: fetch annual fundamentals from Yahoo Finance into `financial_statements`.

Pulls the income statement, balance sheet and cash-flow statement, maps the
relevant line items, and upserts one row per (company, fiscal year).
"""

import pandas as pd
import yfinance as yf

from app.db.database import get_session
from app.db.models import Company
from app.db.repository import upsert_financial
from app.utils.logger import logger

# yfinance line-item labels vary; try each in order
INCOME = {
    "revenue": ["Total Revenue", "Operating Revenue"],
    "net_income": ["Net Income", "Net Income Common Stockholders"],
    "ebit": ["EBIT", "Operating Income"],
    "eps": ["Diluted EPS", "Basic EPS"],
}
BALANCE = {
    "total_assets": ["Total Assets"],
    "total_liabilities": ["Total Liabilities Net Minority Interest"],
    "current_liabilities": ["Current Liabilities"],
    "total_equity": ["Stockholders Equity", "Common Stock Equity",
                     "Total Equity Gross Minority Interest"],
    "shares_outstanding": ["Ordinary Shares Number", "Share Issued"],
}
CASHFLOW = {
    "operating_cash_flow": ["Operating Cash Flow"],
}


def _get(df, labels, col):
    if df is None or df.empty or col not in df.columns:
        return None
    for label in labels:
        if label in df.index:
            val = df.loc[label, col]
            if pd.notna(val):
                return float(val)
    return None


def _load_symbols(limit=None, symbols=None):
    with get_session() as session:
        q = session.query(Company.id, Company.symbol).order_by(Company.id)
        if symbols:
            q = q.filter(Company.symbol.in_(symbols))
        if limit:
            q = q.limit(limit)
        return list(q.all())


def run(limit=None, symbols=None):
    companies = _load_symbols(limit=limit, symbols=symbols)
    logger.info(f"financials_etl: fetching fundamentals for {len(companies)} companies")

    total = 0
    for company_id, symbol in companies:
        try:
            t = yf.Ticker(f"{symbol}.NS")
            inc, bs, cf = t.income_stmt, t.balance_sheet, t.cashflow

            if inc is None or inc.empty:
                continue

            with get_session() as session:
                for col in inc.columns:  # each column is a fiscal period-end
                    fields = {k: _get(inc, labels, col) for k, labels in INCOME.items()}
                    fields.update({k: _get(bs, labels, col) for k, labels in BALANCE.items()})
                    fields.update({k: _get(cf, labels, col) for k, labels in CASHFLOW.items()})

                    # skip periods with no usable data
                    if not any(v is not None for v in fields.values()):
                        continue

                    upsert_financial(
                        session,
                        company_id=company_id,
                        period=f"FY{col.year}",
                        period_type="annual",
                        **fields,
                    )
                    total += 1

        except Exception as e:
            logger.error(f"financials_etl: {symbol} failed: {e}")

    logger.info(f"financials_etl: upserted {total} financial-statement rows")
    return total


if __name__ == "__main__":
    run()
