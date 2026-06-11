import requests
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)

def format_signal_msg(company, ticker, signal, price, timestamp, event, score, text, link):

    emoji = "🟢" if "BUY" in signal.upper() else "🔴"

    return f"""
🚨 *TRADE SIGNAL* 🚨

{emoji} *{signal}*

🏢 {company}
📈 {ticker}
💰 Price: {price}
📌 Event: {event}
⏰ Time: {timestamp}

🧠 Insight: {text}

📊 Confidence: {round(score, 2)}

🔗 [Read More]({link})


"""