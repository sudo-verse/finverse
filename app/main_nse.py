from app.ingestion.unified_fetcher import UnifiedFetcher
from app.nlp.sentiment import get_sentiment
from app.engine.signal import generate_signal
from app.engine.event import detect_event
from app.engine.explain import explain_decision
from app.market.stock_data import get_stock_price
from app.utils.logger import logger
from app.utils.storage import save_signal
from app.utils.telegram import send_telegram, format_signal_msg
import json
import os
import time

STATE_FILE = "engine_state.json"
# Cap the persisted dedup set so it can't grow unbounded across runs
MAX_SEEN = 2000


def load_seen_uids():
    try:
        with open(STATE_FILE, "r") as f:
            return list(json.load(f).get("seen_uids", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_seen_uids(seen_uids):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"seen_uids": seen_uids[-MAX_SEEN:]}, f)
    os.replace(tmp, STATE_FILE)


def process_article(article):
    try:
        text = (article.get("text") or article.get("title") or "")[:512]
        if not text:
            return

        company = article.get("company") or article.get("ticker")
        ticker = article.get("ticker")
        timestamp = article.get("timestamp")
        link = article.get("url", "")
        source = article.get("source", "?")

        if not ticker:
            return

        # --- SENTIMENT ---
        label, score = get_sentiment(text)

        # --- EVENT + SIGNAL ---
        event = detect_event(text)
        signal = generate_signal(label, score, event)

        # --- PRICE (may be unavailable for illiquid stocks; keep signal anyway) ---
        price = get_stock_price(ticker)

        # --- EXPLANATION ---
        explanation = explain_decision(company, event, label, signal)

        # --- SAVE ---
        is_new = save_signal({
            "news": text,
            "company": company,
            "price": price,
            "ticker": ticker,
            "signal": signal,
            "label": label,
            "event": event,
            "score": score,
            "source": source,
            "time": timestamp,
            "uid": article.get("uid"),
        })
        if not is_new:
            return  # already stored (e.g. re-seen after a restart) — don't re-notify

        # Only send BUY signals (avoid spam)
        if signal == "BUY":
            msg = format_signal_msg(
                company, ticker, signal, price, timestamp, event, score, text, link
            )
            send_telegram(msg)

        # --- LOG ---
        logger.info("=" * 60)
        logger.info(f"Source: {source}")
        logger.info(f"Company: {company}")
        logger.info(f"Ticker: {ticker}")
        logger.info(f"Signal: {signal}")
        logger.info(f"Event: {event}")
        logger.info(f"Time: {timestamp}")
        logger.info(f"Price: {price}")
        logger.info(f"Explanation: {explanation}")

    except Exception as e:
        logger.error(f"Processing error: {e}")


def run_cycle(fetcher, seen_uids, seen_set) -> int:
    """One ingestion sweep: fetch all sources, process unseen articles,
    persist the dedup state. Returns the number of new articles processed.

    Shared by the standalone engine loop below and the API's embedded
    background worker (backend.core.engine).
    """
    articles = fetcher.fetch_all()
    if not articles:
        logger.info("No articles found")
        return 0

    new_articles = [a for a in articles if a["uid"] not in seen_set]
    if not new_articles:
        return 0

    logger.info(f"🆕 {len(new_articles)} new articles across all sources")
    for article in new_articles:
        process_article(article)
        seen_set.add(article["uid"])
        seen_uids.append(article["uid"])

    save_seen_uids(seen_uids)
    # Keep the in-memory structures bounded too
    if len(seen_uids) > MAX_SEEN:
        del seen_uids[:-MAX_SEEN]
        seen_set.clear()
        seen_set.update(seen_uids)
    return len(new_articles)


def run():
    logger.info("🚀 Starting Multi-Source Real-Time Engine")

    fetcher = UnifiedFetcher()
    seen_uids = load_seen_uids()
    seen_set = set(seen_uids)

    while True:
        try:
            run_cycle(fetcher, seen_uids, seen_set)
            time.sleep(10)  # ⚡ real-time but safe

        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run()
