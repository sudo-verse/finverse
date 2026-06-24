import pandas as pd
from rapidfuzz import process, utils

# 1. Load the CSV and prepare the mapping
# The CSV has columns: 'Company Name' and 'Symbol'
def load_nifty_map(file_path):
    try:
        df = pd.read_csv(file_path)
        # Create a dictionary: { "Company Name": "SYMBOL.NS" }
        # We add .NS because most financial APIs (yfinance, etc.) require it for NSE
        return dict(zip(df['Company Name'], df['Symbol'] + ".NS"))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

# Full NSE equity universe (all listed equities, not just NIFTY 500)
company_to_ticker = load_nifty_map('nse_equity_list.csv')
def get_best_match(company_name):
    if not company_to_ticker:
        return None, None

    # 2. Extract best match from the CSV keys
    # 'processor=utils.default_process' makes matching case-insensitive and ignores punctuation
    match, score, _ = process.extractOne(
        company_name,
        company_to_ticker.keys(),
        processor=utils.default_process
    )

    # Use a score threshold (70-80 is usually good for official names)
    if score > 79:
        return match, company_to_ticker[match]

    return None, None


def resolve_ticker(text):
    """Extract company names from free text and resolve to a plain NSE symbol.

    Used by news sources (Google News, Moneycontrol, ET) which — unlike NSE
    announcements — don't provide a ticker. Returns (company_name, symbol)
    with the ".NS" suffix stripped so it matches NSE's plain symbols, or
    (None, None) if nothing resolves confidently.
    """
    from app.nlp.ner import extract_companies

    for company in extract_companies(text):
        name, ticker = get_best_match(company)
        if ticker:
            return name, ticker.replace(".NS", "")

    return None, None