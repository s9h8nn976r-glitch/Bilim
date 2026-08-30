import os
import requests
import urllib.parse
from typing import List, Dict

BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/images/search"


def build_google_search_url(query: str) -> str:
    q = urllib.parse.quote(query)
    return f"https://www.google.com/search?q={q}"


def search_bing_images_text(query: str, bing_key: str, count: int = 3) -> List[Dict]:
    """Search Bing Images by text query. Returns list of results with contentUrl and hostPageUrl."""
    if not bing_key:
        return []
    headers = {"Ocp-Apim-Subscription-Key": bing_key}
    params = {"q": query, "count": count}
    try:
        r = requests.get(BING_ENDPOINT, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        results = []
        for item in j.get("value", [])[:count]:
            results.append({
                "contentUrl": item.get("contentUrl"),
                "hostPageUrl": item.get("hostPageUrl"),
                "thumbnailUrl": item.get("thumbnailUrl")
            })
        return results
    except Exception:
        return []


def download_url_to_file(url: str, out_path: str, timeout: int = 15) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=timeout)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(1024 * 8):
                if chunk:
                    f.write(chunk)
        return True
    except Exception:
        return False
