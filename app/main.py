from app.ingestion.news_fetcher import MoneyControlFetcher
from app.nlp.sentiment import get_sentiment
from app.nlp.ner import extract_companies
from app.market.stock_data import get_stock_price
from app.engine.event import detect_event
from app.engine.explain import explain_decision
from app.engine.signal import generate_signal
from app.engine.risk import risk_management
from app.utils.mapping import company_to_ticker
from app.utils.mapping import get_best_match
from app.utils.logger import logger
from app.utils.storage import save_signal
from app.engine.backtest import evaluate_signal
from app.market.stock_data import get_price_on_date

# API_KEY = "12e0310f69e7418b860894acf67838ee"



def run():
    fetcher = MoneyControlFetcher()

    articles = fetcher.fetch_with_retry()

    for article in articles:
        title = article["title"]

        label, score = get_sentiment(title)
        companies = extract_companies(title)

        for company in companies:
            matched_company, ticker = get_best_match(company)
            if ticker:
                price = get_stock_price(ticker)
                if price:
                    event = detect_event(title)
                    signal = generate_signal(label, score , event)
                    print (score)
                    # if(signal == "HOLD"):
                        
                    #     continue    
                    explanation = explain_decision(company, event, label, signal)
                    stop_loss, target = risk_management(price)
                    save_signal({
                        "news": title,
                        "company": matched_company,
                        "ticker": ticker,
                        "signal": signal,
                        "event": event
                    })
                    

                    print("=" * 60)
                    logger.info(f"News: {title}")
                    logger.info(f"Company: {matched_company}")
                    logger.info(f"Ticker: {ticker}")
                    logger.info(f"Event: {event}")
                    logger.info(f"Signal: {signal}")
                    logger.info(f"Explanation: {explanation}")
                    logger.info(f"Stop Loss: {stop_loss}")
                    logger.info(f"Target: {target}")
                    curr_price, prev_price = get_price_on_date(ticker)
                    print(curr_price , prev_price)
                    result = evaluate_signal(signal, prev_price, curr_price)
                    correct = 0
                    total = 0
                    if result is not None:
                        total += 1
                        if result:
                            correct += 1
                    if total > 0:
                        accuracy = correct / total * 100
                        print(f"Accuracy: {accuracy:.2f}%")
                    logger.info(f"Backtest Result: {result}")


if __name__ == "__main__":
    run()