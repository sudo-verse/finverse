import requests
from bs4 import BeautifulSoup

from app.ingestion.base_fetcher import BaseFetcher, make_article
from app.utils.logger import logger
from app.utils.mapping import resolve_ticker


class MoneyControlFetcher(BaseFetcher):

    source = "Moneycontrol"
    URL = "https://www.moneycontrol.com/news/business/stocks/"
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    def fetch(self):
        articles = []

        try:
            res = requests.get(self.URL, headers=self.HEADERS, timeout=10)

            if res.status_code != 200:
                logger.error(f"Moneycontrol failed: {res.status_code}")
                return articles

            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.find_all("li", class_="clearfix")

            for item in items:
                title_tag = item.find("h2")
                link_tag = item.find("a")

                if not title_tag or not link_tag:
                    continue

                title = title_tag.text.strip()
                link = link_tag.get("href", "")

                # News carries no ticker — resolve it from the headline
                company, ticker = resolve_ticker(title)
                if not ticker:
                    continue

                articles.append(make_article(
                    source=self.source,
                    title=title,
                    text=title,
                    company=company,
                    ticker=ticker,
                    url=link,
                    uid=link or title,
                ))

        except Exception as e:
            logger.error(f"Moneycontrol error: {e}")

        return articles
