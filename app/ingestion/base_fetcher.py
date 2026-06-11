from datetime import datetime


def make_article(source, title, text=None, company=None, ticker=None,
                 url="", timestamp=None, uid=None):
    """Build a normalized article that every source emits.

    Fields:
      source    : human-readable source name ("NSE", "Google News", ...)
      title     : headline
      text      : body used for sentiment/event analysis (falls back to title)
      company   : company name (may be None for news sources)
      ticker    : plain NSE symbol WITHOUT the ".NS" suffix (may be None)
      url       : link to the original item
      timestamp : source-provided time (ISO string or source format)
      uid       : stable id used for cross-run/cross-source deduplication
    """
    title = (title or "").strip()
    return {
        "source": source,
        "title": title,
        "text": (text or title or "").strip(),
        "company": company,
        "ticker": ticker,
        "url": url or "",
        "timestamp": timestamp or datetime.now().isoformat(),
        "uid": uid or url or title,
    }


class BaseFetcher:
    source = "base"

    def fetch(self):
        """Return a list of normalized articles (see make_article)."""
        raise NotImplementedError
