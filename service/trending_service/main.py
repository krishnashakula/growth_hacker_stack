import xml.etree.ElementTree as ET
from fastapi import FastAPI

# ``requests`` may not be installed in the test environment.  Provide a small
# stub so that tests patching ``requests.get`` still succeed even when the real
# library isn't available.
try:  # pragma: no cover
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class _RequestsStub:
        def get(self, *a, **k):
            raise ModuleNotFoundError("requests is required")

    requests = _RequestsStub()  # type: ignore

app = FastAPI(title="Trending Keywords Service")


def fetch_trends_rss(geo: str = "US", limit: int = 20):
    """
    Pull the “Trending Now” RSS from Google Trends.
    """
    geo = geo.upper()
    url = (
        "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGRqTVhVU0JXVnVMVlZUR2dKVlV5Z0FQAQ"
        f"?hl=en&gl={geo}&ceid={geo}:en"
    )
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
