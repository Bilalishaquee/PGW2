from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import requests


@dataclass
class SearchHit:
    source_name: str
    title: str
    snippet: str
    url: str
    published_hint: str


def generate_queries() -> list[str]:
    year = datetime.now().year
    return [
        # B2B intent paths
        f"general contractor bidding projects {year}",
        "subcontractor looking for estimating services",
        "hiring construction estimator",
        "project bid deadline site:.com construction",
        "quantity takeoff outsourcing construction",
        "commercial construction bid invitation",
        "plan room public projects bid board",
        # B2C intent paths (residential/homeowner)
        f"homeowner planning renovation contractor quotes {year}",
        "residential remodel project takeoff help",
        "custom home build cost estimate request",
        "home addition estimating services",
        "home renovation bid request",
    ]


def from_serpapi(api_key: str, query: str, limit: int = 10) -> Iterable[SearchHit]:
    if not api_key:
        return []
    params = {"engine": "google", "q": query, "api_key": api_key, "num": limit}
    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    hits: list[SearchHit] = []
    for item in data.get("organic_results", [])[:limit]:
        hits.append(
            SearchHit(
                source_name="serpapi",
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("link", ""),
                published_hint=item.get("date", ""),
            )
        )
    return hits


def from_bing(api_key: str, query: str, limit: int = 10) -> Iterable[SearchHit]:
    if not api_key:
        return []
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "count": limit, "textDecorations": False, "textFormat": "Raw"}
    try:
        resp = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers=headers,
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    hits: list[SearchHit] = []
    for item in data.get("webPages", {}).get("value", [])[:limit]:
        hits.append(
            SearchHit(
                source_name="bing",
                title=item.get("name", ""),
                snippet=item.get("snippet", ""),
                url=item.get("url", ""),
                published_hint=item.get("dateLastCrawled", ""),
            )
        )
    return hits


def discover_hits(serpapi_key: str, bing_api_key: str, per_query_limit: int) -> list[SearchHit]:
    queries = generate_queries()
    all_hits: list[SearchHit] = []
    for q in queries:
        all_hits.extend(from_serpapi(serpapi_key, q, per_query_limit))
        all_hits.extend(from_bing(bing_api_key, q, per_query_limit))
    dedup_urls: set[str] = set()
    unique: list[SearchHit] = []
    for h in all_hits:
        if h.url and h.url not in dedup_urls:
            dedup_urls.add(h.url)
            unique.append(h)
    return unique

