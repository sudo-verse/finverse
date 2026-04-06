import requests
import time
BOT_TOKEN = "8685652065:AAEYp-PFLNATwKciLDKhYrZJH3PyZrULccU"
CHAT_ID = "1873512150"


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
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