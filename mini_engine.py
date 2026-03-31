import requests
from transformers import pipeline
import spacy
import yfinance as yf

# Load models once
sentiment_model = pipeline("sentiment-analysis")
nlp = spacy.load("en_core_web_sm")

# Mapping (basic)
company_to_ticker = {
    "Reliance Industries": "RELIANCE.NS",
    "Infosys": "INFY.NS",
    "TCS": "TCS.NS",
    "Wipro": "WIPRO.NS",
    "American Airlines": "AAL",
    "Meta": "META",
    "Bank of America": "BAC",
    "Pershing Square": "PSH"
}

# ---------------- FUNCTIONS ---------------- #

def fetch_news(api_key):
    url = f"https://newsapi.org/v2/everything?q=stock%20market&apiKey={api_key}"
    data = requests.get(url).json()
    return data["articles"]


def get_sentiment(text):
    result = sentiment_model(text)[0]
    return result["label"], result["score"]


def extract_companies(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "ORG"]


def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        return data["Close"].iloc[-1]
    return None


def generate_signal(label, score):
    if label == "POSITIVE" and score > 0.7:
        return "BUY"
    elif label == "NEGATIVE" and score > 0.7:
        return "SELL"
    else:
        return "HOLD"


def risk_management(price):
    stop_loss = price * 0.98
    target = price * 1.04
    return stop_loss, target


# ---------------- MAIN PIPELINE ---------------- #

def run_engine(api_key):
    articles = fetch_news(api_key)

    for article in articles[:15]:
        title = article["title"]
        # print(title)

        # Sentiment
        label, score = get_sentiment(title)

        # Companies
        companies = extract_companies(title)

        for company in companies:
            if company in company_to_ticker:
                ticker = company_to_ticker[company]

                price = get_stock_price(ticker)

                if price:
                    signal = generate_signal(label, score)
                    stop_loss, target = risk_management(price)

                    print("=" * 60)
                    print("News:", title)
                    print("Company:", company)
                    print("Ticker:", ticker)
                    print("Price:", round(price, 2))
                    print("Sentiment:", label, round(score, 2))
                    print("Signal:", signal)
                    print("Stop Loss:", round(stop_loss, 2))
                    print("Target:", round(target, 2))


# ---------------- RUN ---------------- #

API_KEY = "12e0310f69e7418b860894acf67838ee"
run_engine(API_KEY)