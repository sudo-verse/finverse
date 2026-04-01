import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from app.utils.logger import logger

URL = "https://www.moneycontrol.com/news/business/stocks/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Connection": "keep-alive"
}


class MoneyControlFetcher:
    def __init__(self):
        self.seen_links = set()

    def fetch_news(self):
        try:
            res = requests.get(URL, headers=HEADERS, timeout=10)

            if res.status_code != 200:
                logger.error(f"Failed request: {res.status_code}")
                return []

            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.find_all("li", class_="clearfix")

            news_list = []

            for article in articles:
                title_tag = article.find("h2")
                link_tag = article.find("a")

                if not title_tag or not link_tag:
                    continue

                title = title_tag.text.strip()
                link = link_tag["href"]

                # Deduplication
                if link in self.seen_links:
                    continue

                self.seen_links.add(link)

                news_list.append({
                    "title": title,
                    "url": link,
                    "source": "Moneycontrol",
                    "timestamp": datetime.now().isoformat()
                })

            return news_list

        except Exception as e:
            logger.error(f"Scraper error: {e}")
            return []

    def fetch_with_retry(self, retries=3, delay=2):
        for attempt in range(retries):
            news = self.fetch_news()

            if news:
                return news

            logger.warning(f"Retry {attempt + 1} failed...")
            time.sleep(delay)

        return []
    


    def fetch_full_article(self , url):
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            # Moneycontrol article paragraphs
            paragraphs = soup.find_all("p")

            text = " ".join([p.get_text(strip=True) for p in paragraphs])

            return text

        except Exception as e:
            return ""