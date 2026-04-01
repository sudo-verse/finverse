# from app.ingestion.unified_fetcher import UnifiedFetcher
from app.ingestion.nse_fetcher import fetch_nse_announcements
from app.ingestion.article_extractor import fetch_full_article
from app.nlp.sentiment import get_sentiment
from app.nlp.ner import extract_companies
from app.market.stock_data import get_stock_price
from app.engine.event import detect_event
from app.engine.explain import explain_decision
from app.engine.signal import generate_signal
from app.engine.keyword_engine import keyword_signal, final_signal
from app.engine.risk import risk_management
from app.utils.mapping import company_to_ticker
from app.utils.mapping import get_best_match
from app.utils.logger import logger
from app.utils.storage import save_signal
from app.engine.backtest import evaluate_signal
from app.market.stock_data import get_price_on_date
import time

def run():
    
    # fetcher = UnifiedFetcher()
    

    seen_news = set()
    correct = 0
    total = 0

    while True:
        logger.info("Fetching news...")

        # articles = fetcher.fetch_all()
        articles = fetch_nse_announcements()
        for article in articles:
            # title = article["title"]
            title = article["attchmntText"]
            

            if title in seen_news:
                continue

            seen_news.add(title)

            # if len(title) < 40:
            #     full_text = fetch_full_article(article["url"])
            # else:
            #     full_text = ""

            # fallback if scraping fails
            
            # text_to_analyze = full_text if full_text else title
            # text_to_analyze = text_to_analyze[:512]

            # label, score = get_sentiment(text_to_analyze)
            # companies = extract_companies(title)
            label,score=get_sentiment(title)
            
            companies = article['sm_name']
            ticker=article['symbol']

            if not companies:
                continue
            price=get_stock_price(ticker)
            if price is None:
                price = 0

            event=detect_event(article['desc'])
            k_signal,k_score,matches=keyword_signal(article['desc'])
            signal=final_signal(label,score,k_signal,k_score)
            explanation=explain_decision(companies,event,label,signal)
            stop_loss,target=risk_management(price)
            save_signal({
                "news":title,
                "company":companies,
                "ticker":ticker,
                "signal":signal,
                "event":event
            })
            logger.info("=" * 60)
            logger.info(f"News: {title}")
            logger.info(f"Company: {companies}")
            logger.info(f"Signal: {signal}")

                    # Backtesting only for actionable signals
            if signal in ["BUY", "SELL", "STRONG BUY", "STRONG SELL"]:
                curr_price, prev_price = get_price_on_date(ticker)

                result = evaluate_signal(signal, prev_price, curr_price)

                if result is not None:
                    total += 1
                    if result:
                        correct += 1

                    accuracy = (correct / total) * 100
                    logger.info(f"Accuracy: {accuracy:.2f}%")

        #     for company in companies:
        #         matched_company, ticker = get_best_match(company)

        #         if not ticker:
        #             continue

        #         price = get_stock_price(ticker)

        #         if price is None:
        #             continue

        #         event = detect_event(title)
                
        #         k_signal, k_score, matches = keyword_signal(text_to_analyze)

        #         signal = final_signal(label, score, k_signal, k_score)

        #         explanation = explain_decision(company, event, label, signal)
        #         stop_loss, target = risk_management(price)

        #         save_signal({
        #             "news": title,
        #             "company": matched_company,
        #             "ticker": ticker,
        #             "signal": signal,
        #             "event": event
        #         })

        #         logger.info("=" * 60)
        #         logger.info(f"News: {title}")
        #         logger.info(f"Company: {matched_company}")
        #         logger.info(f"Signal: {signal}")

        #         # Backtesting only for actionable signals
        #         if signal in ["BUY", "SELL", "STRONG BUY", "STRONG SELL"]:
        #             curr_price, prev_price = get_price_on_date(ticker)

        #             result = evaluate_signal(signal, prev_price, curr_price)

        #             if result is not None:
        #                 total += 1
        #                 if result:
        #                     correct += 1

        #                 accuracy = (correct / total) * 100
        #                 logger.info(f"Accuracy: {accuracy:.2f}%")

        #
        time.sleep(60)

if __name__ == "__main__":
    run()