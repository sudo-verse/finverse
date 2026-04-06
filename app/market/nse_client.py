import requests
import time


class NSEClient:
    def __init__(self):
        self.session = requests.Session()

        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/"
        }

        self.base_url = "https://www.nseindia.com"
        self.api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"

        # cache
        self.cache = None
        self.last_fetch = 0

        # initialize session
        self.session.get(self.base_url, headers=self.headers)

    def get_data(self):
        now = time.time()

        # cache for 5 sec
        if self.cache and (now - self.last_fetch < 5):
            return self.cache

        try:
            res = self.session.get(self.api_url, headers=self.headers, timeout=5)

            if res.status_code == 200:
                self.cache = res.json()["data"]
                self.last_fetch = now
                return self.cache

        except Exception as e:
            print("NSE API error:", e)

        return None

    def get_price(self, symbol):
        data = self.get_data()

        if not data:
            return None

        for stock in data:
            if stock["symbol"] == symbol:
                return float(stock["lastPrice"])

        return None

