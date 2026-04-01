import requests
from bs4 import BeautifulSoup
from datetime import datetime
from app.utils.logger import logger
from .base_fetcher import BaseFetcher


class MoneyControlFetcher(BaseFetcher):

    URL = "https://www.moneycontrol.com/news/business/stocks/"
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    def __init__(self):
        self.seen_links = set()

    def fetch(self):
        try:
            res = requests.get(self.URL, headers=self.HEADERS, timeout=10)

            if res.status_code != 200:
                logger.error(f"Moneycontrol failed: {res.status_code}")
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
            logger.error(f"Moneycontrol error: {e}")
            return []