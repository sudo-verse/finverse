from app.ingestion.nse_fetcher import fetch_nse_announcements
from app.nlp.sentiment import get_sentiment
from app.engine.signal import generate_signal
from app.engine.event import detect_event
from app.engine.explain import explain_decision
from app.market.stock_data import get_stock_price
from app.utils.logger import logger
from app.utils.storage import save_signal
import time


def process_article(article):
    try:
        # --- SAFE TEXT ---
        text = article.get("attchmntText") or article.get("desc") or ""
        text = text[:512]

        if not text:
            return

        # --- BASIC INFO ---
        company = article["sm_name"]
        ticker = article["symbol"] + ".NS"
        timestamp = article["sort_date"]

        # --- SENTIMENT ---
        label, score = get_sentiment(text)

        ## --- EVENT ---
        event = detect_event(text)
        signal = generate_signal(label, score, event)

        # --- FINAL SIGNAL ---
        if signal == "HOLD":
            print(company, "=> HOLD => ",score)
            return

        

        # --- PRICE ---
        price = get_stock_price(ticker)
        if price is None:
            return

        # --- EXPLANATION ---
        explanation = explain_decision(company, text, label, signal)

        # --- SAVE ---
        save_signal({
            "news": text,
            "company": company,
            "ticker": ticker,
            "signal": signal,
            "event": event,
            "score": score,
            "time": timestamp
        })

        # --- LOG ---
        logger.info("=" * 60)
        logger.info(f"Company: {company}")
        logger.info(f"Ticker: {ticker}")
        logger.info(f"Signal: {signal}")
        logger.info(f"Event: {event}")
        logger.info(f"Sentiment: {label} ({score:.2f})")
        logger.info(f"Time: {timestamp}")
        logger.info(f"Price: {price}")
        logger.info(f"Explanation: {explanation}")

    except Exception as e:
        logger.error(f"Processing error: {e}")


def run():
    logger.info("🚀 Starting NSE Real-Time Engine")

    last_seq_id = None

    while True:
        try:
            articles = fetch_nse_announcements()
            if not articles:
                time.sleep(10)
                print("No articles found")
                continue

            new_articles = []

            for article in articles:
                if last_seq_id is None or article["seq_id"] > last_seq_id:
                    new_articles.append(article)

            # Update latest seen
            last_seq_id = articles[0]["seq_id"]

            if new_articles:
                logger.info(f"🆕 {len(new_articles)} new announcements")
                i=0

            # Process oldest first
            for article in reversed(new_articles):
                process_article(article)

            time.sleep(10)  # ⚡ real-time but safe
            i=i+1
            print(i)

        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(10)
            print("=" * 60)


if __name__ == "__main__":
    run()