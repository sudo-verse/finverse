import yfinance as yf

df = yf.download(
    "RELIANCE.NS",
    start="2026-04-09",
    end="2026-04-10",
    interval="1m"
)

print(df.head())