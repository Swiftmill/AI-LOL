from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Iterable, List

import requests
from duckduckgo_search import DDGS
from requests import Response

HEADERS = {"User-Agent": "AI-Local/1.0 (+https://example.local)"}
TIMEOUT = 10
MAX_PAGES = 5


VALID_URL = re.compile(r"^https?://")


def ddg_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    with DDGS() as ddgs:
        results = ddgs.text(query, region="wt-wt", safesearch="moderate", max_results=max_results)
        return [
            {"title": item.get("title", ""), "href": item.get("href", ""), "body": item.get("body", "")}
            for item in results
            if item.get("href") and VALID_URL.match(item["href"])
        ]


def fetch_url(url: str) -> Dict[str, str]:
    if not VALID_URL.match(url):
        return {"url": url, "content": ""}
    try:
        resp: Response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code >= 400:
            return {"url": url, "content": ""}
        content = resp.text[:500000]
        return {"url": url, "content": content}
    except requests.RequestException:
        return {"url": url, "content": ""}


def clean_html(html: str) -> str:
    if not html:
        return ""
    try:
        from bs4 import BeautifulSoup
        from readability import Document
    except Exception:
        return html
    try:
        doc = Document(html)
        summary = doc.summary()
        soup = BeautifulSoup(summary, "html.parser")
        return soup.get_text(" ", strip=True)
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(" ", strip=True)


def fetch_many(urls: Iterable[str]) -> List[Dict[str, str]]:
    pages: List[Dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(fetch_url, url): url for url in list(urls)[:MAX_PAGES]}
        for future in as_completed(future_map):
            result = future.result()
            if result.get("content"):
                result["text"] = clean_html(result["content"])
                pages.append(result)
    return pages

