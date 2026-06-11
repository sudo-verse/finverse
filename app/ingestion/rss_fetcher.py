import xml.etree.ElementTree as ET

import requests

from app.ingestion.base_fetcher import BaseFetcher, make_article
from app.utils.logger import logger
from app.utils.mapping import resolve_ticker
from app.utils.text import strip_html


class RSSFetcher(BaseFetcher):
    """Generic RSS source.

    Subclasses set `source` and `URL`. Items whose company can't be resolved
    to a known NSE ticker are dropped (news without an actionable stock is
    noise for this engine).
    """

    source = "rss"
    URL = ""
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    def fetch(self):
        articles = []

        try:
            res = requests.get(self.URL, headers=self.HEADERS, timeout=10)
            if res.status_code != 200:
                logger.error(f"{self.source} RSS failed: {res.status_code}")
                return articles

            root = ET.fromstring(res.content)

            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                if not title:
                    continue

                link = (item.findtext("link") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                # Google News (and some other feeds) ship raw HTML here —
                # strip it so sentiment/event analysis and the stored
                # headline work on clean text.
                description = strip_html(item.findtext("description"))

                company, ticker = resolve_ticker(title)
                if not ticker:
                    continue

                articles.append(make_article(
                    source=self.source,
                    title=title,
                    text=description or title,
                    company=company,
                    ticker=ticker,
                    url=link,
                    timestamp=pub_date,
                    uid=link or title,
                ))

        except ET.ParseError as e:
            logger.error(f"{self.source} RSS parse error: {e}")
        except Exception as e:
            logger.error(f"{self.source} RSS error: {e}")

        return articles


class GoogleNewsFetcher(RSSFetcher):
    source = "Google News"
    URL = ("https://news.google.com/rss/headlines/section/topic/BUSINESS"
           "?hl=en-IN&gl=IN&ceid=IN:en")


class EconomicTimesFetcher(RSSFetcher):
    source = "Economic Times"
    # ET Markets > Stocks RSS feed
    URL = "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"
