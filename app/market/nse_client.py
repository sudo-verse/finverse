import os
import requests
import time


class NSEClient:
    NEXT_API_URL = "https://www.nseindia.com/api/NextApi/apiClient"
    QUOTE_API_URL = NEXT_API_URL + "/GetQuoteApi"
    HOME_API_URL = NEXT_API_URL + "/homeApi"

    def __init__(self):
        self.session = requests.Session()

        # Route traffic through a proxy if configured (e.g. on Hugging Face Spaces)
        nse_proxy = os.getenv("NSE_PROXY")
        if nse_proxy:
            self.session.proxies = {
                "http": nse_proxy,
                "https": nse_proxy,
            }

        self.nse_api_base_url = os.getenv("NSE_API_BASE_URL")
        if self.nse_api_base_url:
            self.nse_api_base_url = self.nse_api_base_url.rstrip("/")

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
        if not self.nse_api_base_url:
            self.session.get(self.base_url, headers=self.headers)

    def get_data(self):
        now = time.time()

        # cache for 5 sec
        if self.cache and (now - self.last_fetch < 5):
            return self.cache

        if self.nse_api_base_url:
            try:
                res = self.session.get(f"{self.nse_api_base_url}/nse/equity-stockIndices", timeout=10)
                if res.status_code == 200:
                    self.cache = res.json().get("data")
                    self.last_fetch = now
                    return self.cache
            except Exception as e:
                print("NSE API proxy error (get_data):", e)
            return None

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
        # Fast path: symbol is in the cached NIFTY 500 index data
        data = self.get_data()

        if data:
            for stock in data:
                if stock["symbol"] == symbol:
                    return float(stock["lastPrice"])

        # Fallback: Yahoo Finance covers all listed equities, not just
        # NIFTY 500 constituents (NSE symbols map to "<symbol>.NS")
        return self.get_yahoo_price(symbol)

    def quote_api(self, function_name, **params):
        """NextApi GetQuoteApi — symbol-scoped data (quote, filings, peers…)."""
        return self._next_api_get(self.QUOTE_API_URL, function_name, params)

    def next_api(self, function_name, **params):
        """NextApi apiClient — market-wide data (index data, GIFT Nifty…)."""
        return self._next_api_get(self.NEXT_API_URL, function_name, params)

    def home_api(self, function_name, **params):
        """NextApi homeApi — homepage widgets (curated indices set…)."""
        return self._next_api_get(self.HOME_API_URL, function_name, params)

    def _next_api_get(self, url, function_name, params):
        """GET a NextApi endpoint with the session cookies.

        Returns the parsed JSON, or None on failure. Retries once after
        re-doing the homepage handshake (NSE cookies expire).
        """
        query = {"functionName": function_name, **params}

        if self.nse_api_base_url:
            if url == self.QUOTE_API_URL:
                path = "/nse/quote"
            elif url == self.NEXT_API_URL:
                path = "/nse/next"
            else:
                path = "/nse/home"
            try:
                res = self.session.get(f"{self.nse_api_base_url}{path}", params=query, timeout=10)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                print(f"NSE API proxy error ({function_name}):", e)
            return None

        for attempt in (1, 2):
            try:
                res = self.session.get(url, params=query, headers=self.headers, timeout=10)
                if res.status_code == 200:
                    return res.json()
                # 401/403 → cookies stale; refresh and retry once
                if attempt == 1:
                    self.session.get(self.base_url, headers=self.headers, timeout=10)
            except Exception as e:
                print(f"NSE NextApi error ({function_name}, try {attempt}):", e)
                if attempt == 1:
                    try:
                        self.session.get(self.base_url, headers=self.headers, timeout=10)
                    except Exception:
                        pass
        return None

    def get_yahoo_price(self, symbol):
        try:
            import yfinance as yf

            ticker = yf.Ticker(f"{symbol}.NS")

            # fast_info.last_price is the cheapest path; fall back to the
            # latest daily close if it isn't populated
            price = ticker.fast_info.last_price

            if price is None:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]

            if price is not None:
                return float(price)

        except Exception as e:
            print(f"Yahoo price error for {symbol}:", e)

        return None

