from app.ingestion.nse_fetcher import NSEFetcher
from app.ingestion.rss_fetcher import GoogleNewsFetcher, EconomicTimesFetcher
from app.ingestion.moneycontrol_fetcher import MoneyControlFetcher
from app.utils.logger import logger


class UnifiedFetcher:
    """Aggregate normalized articles from every configured source.

    Each fetcher is isolated so one failing source never blocks the others.
    Results are deduplicated within a single sweep by `uid` and by a
    normalized title (to catch the same story reported by two sources).
    """

    def __init__(self):
        self.fetchers = [
            NSEFetcher(),
            GoogleNewsFetcher(),
            MoneyControlFetcher(),
            EconomicTimesFetcher(),
        ]

    def fetch_all(self):
        all_articles = []
        seen_uids = set()
        seen_titles = set()

        for fetcher in self.fetchers:
            try:
                articles = fetcher.fetch()
                logger.info(f"{fetcher.source}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"{fetcher.source} fetcher failed: {e}")
                continue

            for article in articles:
                uid = article["uid"]
                title_key = article["title"].lower()

                if uid in seen_uids or title_key in seen_titles:
                    continue

                seen_uids.add(uid)
                seen_titles.add(title_key)
                all_articles.append(article)

        return all_articles
