import requests

def fetch_nse_announcements():
    url = "https://www.nseindia.com/api/corporate-announcements?index=equities"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)

    response = session.get(url, headers=headers)

    return response.json()
