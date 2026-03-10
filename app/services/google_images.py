from __future__ import annotations

from urllib.parse import quote_plus, urlsplit, urlunsplit


def _normalize_img_value(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    if " " in value and "http" in value:
        value = value.split(" ")[0]
    return value


def _canonicalize(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def _is_candidate_url(url: str) -> bool:
    if not url.startswith("http"):
        return False
    bad_hosts = ("gstatic.com", "googleusercontent.com")
    if any(host in url for host in bad_hosts):
        return False
    bad_tokens = ("sprite", "sheet", "logo", "set", "pack", "collection", "watermark")
    low = url.lower()
    return not any(token in low for token in bad_tokens)


async def collect_google_image_urls(page, query: str, limit: int = 10) -> list[str]:
    encoded = quote_plus(query)
    target_url = f"https://www.google.com/search?tbm=isch&q={encoded}"
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
              const dataSrc = el.getAttribute('data-src');
              if (src) out.push(src);
              if (dataSrc) out.push(dataSrc);
              if (srcset) {
                for (const part of srcset.split(',')) {
                  out.push(part.trim());
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
            candidate = _canonicalize(candidate)
            if candidate in seen:
                continue
            seen.add(candidate)
            urls.append(candidate)
            if len(urls) >= limit:
                return urls

        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1200)

    return urls
