from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Callable

from playwright.async_api import async_playwright

from .elements import build_50_elements
from .excel_export import write_excel
from .google_images import collect_google_image_urls
from .pinterest import collect_pinterest_urls


ProgressCallback = Callable[[str, int, int, str], None]


def _sanitize_filename(text: str) -> str:
    keep = []
    for ch in text.strip():
        if ch.isalnum() or ch in {"-", "_"}:
            keep.append(ch)
        elif ch == " ":
            keep.append("_")
    return "".join(keep)[:60] or "theme"


async def _collect_for_element(context, theme: str, element: str, limit: int) -> tuple[str, list[str], str]:
    page = await context.new_page()
    try:
        queries = [
            f"{theme} {element} c4d 3d cute single icon isolated -set -pack -collection",
            f"{theme} {element} 3d kawaii icon single object clean background",
            f"{element} c4d 3d icon single object",
        ]
        merged: list[str] = []
        seen: set[str] = set()
        chosen_query = queries[0]

        for query in queries:
            # Prefer Pinterest first, then Google Images as fallback.
            urls = await collect_pinterest_urls(page, query, limit=limit)
            if len(urls) < limit:
                google_urls = await collect_google_image_urls(page, query, limit=limit)
                urls.extend(google_urls)
            if urls:
                chosen_query = query
            for url in urls:
                if url in seen:
                    continue
                seen.add(url)
                merged.append(url)
                if len(merged) >= limit:
                    return element, merged, chosen_query
        return element, merged, chosen_query
    finally:
        await page.close()


async def generate_theme_excel(
    theme: str,
    output_dir: Path,
    progress_callback: ProgressCallback | None = None,
    per_element_limit: int = 10,
    element_limit: int = 50,
) -> Path:
    elements = build_50_elements(theme)[:element_limit]
    total = len(elements)
    rows: list[dict] = []

    if progress_callback:
        progress_callback("starting", 0, total, "")

    local_app_data = os.getenv("LOCALAPPDATA", "")
    fallback_executable = Path(local_app_data) / "ms-playwright" / "chromium-1208" / "chrome-win64" / "chrome.exe"
    launch_kwargs = {"headless": True}
    if fallback_executable.exists():
        launch_kwargs["executable_path"] = str(fallback_executable)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(**launch_kwargs)
        context = await browser.new_context()

        semaphore = asyncio.Semaphore(4)
        done = 0

        async def worker(element: str):
            nonlocal done
            async with semaphore:
                result = await _collect_for_element(context, theme, element, per_element_limit)
                done += 1
                if progress_callback:
                    progress_callback("collecting", done, total, element)
                return result

        tasks = [asyncio.create_task(worker(element)) for element in elements]
        all_results = await asyncio.gather(*tasks)
        await context.close()
        await browser.close()

    global_seen: set[str] = set()
    for element, urls, query in all_results:
        deduped_urls: list[str] = []
        for image_url in urls:
            if image_url in global_seen:
                continue
            global_seen.add(image_url)
            deduped_urls.append(image_url)

        for idx, image_url in enumerate(deduped_urls, start=1):
            rows.append(
                {
                    "theme": theme,
                    "element": element,
                    "image_index": idx,
                    "search_query": query,
                    "image_url": image_url,
                    "source": "pinterest",
                }
            )

    if progress_callback:
        progress_callback("exporting", 0, 1, "")

    output_name = f"{_sanitize_filename(theme)}_icon_references.xlsx"
    output_path = output_dir / output_name
    final_path = write_excel(rows, output_path)

    if progress_callback:
        progress_callback("exporting", 1, 1, "")
        progress_callback("finished", total, total, "")

    return final_path
