from __future__ import annotations

import re
from urllib.parse import quote_plus

import requests


def collect_duckduckgo_urls_http(query: str, limit: int = 10) -> list[str]:
    base_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    q = quote_plus(query)
    search_url = f"https://duckduckgo.com/?q={q}&iax=images&ia=images"

    try:
        resp = requests.get(search_url, headers=base_headers, timeout=(6, 12))
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return []

    m = re.search(r"vqd=['\"]([^'\"]+)['\"]", html)
    if not m:
        m = re.search(r"vqd=([0-9-]+)\&", html)
    if not m:
        return []
    vqd = m.group(1)

    api_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={q}&vqd={vqd}&f=,,,,,&p=1"
    try:
        api_resp = requests.get(
            api_url,
            headers={**base_headers, "Referer": "https://duckduckgo.com/"},
            timeout=(6, 12),
        )
        api_resp.raise_for_status()
        payload = api_resp.json()
    except Exception:
        return []

    out: list[str] = []
    seen: set[str] = set()
    for item in payload.get("results", []):
        url = (item.get("image") or "").strip()
        if not url.startswith("http"):
            continue
        low = url.lower()
        if any(x in low for x in ("sprite", "logo", "set", "pack", "collection", "iconfont")):
            continue
        clean = url.split("?")[0]
        if clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
        if len(out) >= limit:
            break

    return out
