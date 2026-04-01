from app.ingestion.moneycontrol_fetcher import MoneyControlFetcher
from app.utils.logger import logger


class UnifiedFetcher:

    def __init__(self):
        self.fetchers = [
            MoneyControlFetcher(),
            # Future:
            # NSEFetcher(),
            # GoogleNewsFetcher()
        ]

    def fetch_all(self):
        all_news = []

        for fetcher in self.fetchers:
            try:
                data = fetcher.fetch()
                logger.info(f"{fetcher.__class__.__name__}: {len(data)} articles")

                all_news.extend(data)

            except Exception as e:
                logger.error(f"Fetcher failed: {e}")

        return all_news