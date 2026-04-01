import requests
from bs4 import BeautifulSoup
from app.utils.logger import logger

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_full_article(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            return ""

        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.find_all("p")

        text = " ".join([p.get_text(strip=True) for p in paragraphs])

        return text

    except Exception as e:
        logger.error(f"Article fetch error: {e}")
        return ""