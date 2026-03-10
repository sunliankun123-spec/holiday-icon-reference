from __future__ import annotations

import re
from urllib.parse import quote_plus
from urllib.parse import urlsplit, urlunsplit


def _normalize_img_value(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    if " " in value and "http" in value:
        value = value.split(" ")[0]
    return value


def _to_original_pinimg_url(url: str) -> str:
    if "pinimg.com" not in url:
        return url
    # Promote thumbnail-sized Pinterest URLs to originals path.
    # Example: /236x/... -> /originals/...
    return re.sub(r"/(?:\d+x|originals)/", "/originals/", url, count=1)


def _canonicalize_url(url: str) -> str:
    parsed = urlsplit(url)
    clean = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return _to_original_pinimg_url(clean)


def _is_candidate_url(url: str) -> bool:
    if not url.startswith("http"):
        return False
    if "pinimg.com" not in url:
        return False
    bad_tokens = ("/30x30/", "/60x60/", "/75x75/", "default_")
    return not any(token in url for token in bad_tokens)


async def collect_pinterest_urls(page, query: str, limit: int = 10) -> list[str]:
    encoded = quote_plus(query)
    target_url = f"https://www.pinterest.com/search/pins/?q={encoded}"
    await page.goto(target_url, wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_timeout(2200)

    urls: list[str] = []
    seen: set[str] = set()

    for _ in range(9):
        found = await page.eval_on_selector_all(
            "img",
            """
            (els) => els.flatMap((el) => {
              const out = [];
              const src = el.getAttribute('src');
              const srcset = el.getAttribute('srcset');
              let best = null;
              if (src) out.push(src);
              if (srcset) {
                const parts = srcset
                  .split(',')
                  .map(p => p.trim())
                  .filter(Boolean);
                if (parts.length > 0) {
                  best = parts[parts.length - 1];
                  out.unshift(best);
                }
              }
              return out;
            })
            """,
        )

        for raw in found:
            candidate = _normalize_img_value(raw)
            if not _is_candidate_url(candidate):
                continue
            candidate = _canonicalize_url(candidate)
            if candidate in seen:
                continue
            seen.add(candidate)
            urls.append(candidate)
            if len(urls) >= limit:
                return urls

        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1200)

    return urls
