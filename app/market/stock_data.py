import yfinance as yf

def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")

    if not data.empty:
        return data["Close"].iloc[-1]
    return None

def get_price_on_date(ticker, days=1):
    import yfinance as yf

    stock = yf.Ticker(ticker)
    data = stock.history(period=f"{days+1}d")
    if len(data) >= 2:
        return data["Close"].iloc[-1], data["Close"].iloc[-2]

    return None, None