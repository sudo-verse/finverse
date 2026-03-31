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

# Initialize the data from your uploaded file
company_to_ticker = load_nifty_map('ind_nifty500list.csv')
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
    if score > 90:
        return match, company_to_ticker[match]

    return None, None