import requests

from app.ingestion.base_fetcher import BaseFetcher, make_article
from app.utils.logger import logger


def fetch_nse_announcements():
    url = "https://www.nseindia.com/api/corporate-announcements?index=equities"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)

    response = session.get(url, headers=headers)

    try:
        data = response.json()
    except ValueError:
        # NSE frequently returns HTML / 401 when rate-limited
        logger.error(f"NSE returned non-JSON (status {response.status_code})")
        return []

    return data if isinstance(data, list) else []


class NSEFetcher(BaseFetcher):
    source = "NSE"

    def fetch(self):
        articles = []

        for a in fetch_nse_announcements():
            desc = a.get("desc") or ""
            attachment_text = a.get("attchmntText") or ""
            # Combine both so event/sentiment analysis sees all the text
            text = " ".join(p for p in [desc, attachment_text] if p).strip()

            articles.append(make_article(
                source=self.source,
                title=desc or attachment_text,
                text=text,
                company=a.get("sm_name"),
                ticker=a.get("symbol"),
                url=a.get("attchmntFile", ""),
                timestamp=a.get("sort_date"),
                uid=f"NSE:{a.get('seq_id')}",
            ))

        return articles
