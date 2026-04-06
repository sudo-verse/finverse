import yfinance as yf

def get_snapshot(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d", interval="1m")


        if data.empty:
            return None

        last = data.iloc[-1]


        return {
           
            "price": float(last["Close"]),
            "volume": float(last["Volume"])
        }

    except:
        return None
