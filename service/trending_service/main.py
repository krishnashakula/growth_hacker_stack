import xml.etree.ElementTree as ET
import requests
from fastapi import FastAPI

app = FastAPI(title="Trending Keywords Service")


def fetch_trends_rss(geo: str = "US", limit: int = 20):
    """
    Pull the “Trending Now” RSS from Google Trends.
    """
    url = f"https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGRqTVhZU0JXVnVMVlZUR2dKVlV5Z0FQAQ?hl=en-US&gl=US&ceid=US:en{geo}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    titles = []
    for item in root.findall(".//item"):
        text = item.findtext("title")
        if text:
            titles.append(text.strip())
        if len(titles) >= limit:
            break
    return titles


@app.get("/keywords", summary="Get top trending search terms")
def keywords(geo: str = "US", limit: int = 20):
    return {"keywords": fetch_trends_rss(geo=geo.upper(), limit=limit)}
