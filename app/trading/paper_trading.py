from app.market.stock_data import get_stock_price
from app.utils.logger import logger


portfolio = []


def execute_paper_trade(signal, ticker, company):

    if signal not in ["BUY", "SELL", "STRONG BUY", "STRONG SELL"]:
        return

    price = get_stock_price(ticker)

    if price is None:
        return

    trade = {
        "company": company,
        "ticker": ticker,
        "signal": signal,
        "entry_price": price,
        "status": "OPEN"
    }

    portfolio.append(trade)

    logger.info("📈 PAPER TRADE OPENED")
    logger.info(trade)

def update_portfolio():
        for trade in portfolio:

            if trade["status"] != "OPEN":
                continue

            current_price = get_stock_price(trade["ticker"])

            if current_price is None:
                continue

            entry = trade["entry_price"]

            if "BUY" in trade["signal"]:
                pnl = current_price - entry
            else:
                pnl = entry - current_price

            trade["pnl"] = round(pnl, 2)
            trade["current_price"] = current_price

            logger.info(f"📊 PnL Update: {trade['ticker']} → {pnl}")