from __future__ import annotations

import re
from urllib.parse import quote_plus

import requests


def collect_bing_urls_http(query: str, limit: int = 10) -> list[str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    q = quote_plus(query)
    url = f"https://www.bing.com/images/search?q={q}&form=HDRSC3&first=1&tsc=ImageHoverTitle"
    try:
        resp = requests.get(url, headers=headers, timeout=(6, 12))
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return []

    # Bing stores original image url in murl field.
    patterns = [
        r"murl&quot;:&quot;(https?://[^&]+?)&quot;",
        r"\"murl\":\"(https?://[^\"]+)\"",
    ]
    candidates: list[str] = []
    for pat in patterns:
        candidates.extend(re.findall(pat, html, flags=re.IGNORECASE))

    out: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        clean = raw.replace("\\/", "/").split("?")[0].strip()
        if not clean.startswith("http"):
            continue
        low = clean.lower()
        if any(x in low for x in ("sprite", "logo", "set", "pack", "collection", "iconfont")):
            continue
        if clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
        if len(out) >= limit:
            break
    return out
