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


def _resolve_chromium_executable() -> str | None:
    # Windows local dev fallback.
    local_app_data = os.getenv("LOCALAPPDATA", "")
    win_candidate = Path(local_app_data) / "ms-playwright" / "chromium-1208" / "chrome-win64" / "chrome.exe"
    if win_candidate.exists():
        return str(win_candidate)

    # Linux Render/cache fallback.
    linux_roots = [
        Path("/opt/render/.cache/ms-playwright"),
        Path.home() / ".cache" / "ms-playwright",
        Path("~/.cache/ms-playwright").expanduser(),
    ]
    patterns = ("chromium-*/chrome-linux/chrome", "chromium-*/chrome-linux64/chrome")
    for root in linux_roots:
        if not root.exists():
            continue
        for pattern in patterns:
            matches = sorted(root.glob(pattern))
            if matches:
                return str(matches[-1])

    # PLAYWRIGHT_BROWSERS_PATH=0 fallback (local browsers in package directory).
    pkg_root = Path(__file__).resolve().parents[3]
    local_browser_roots = [
        pkg_root / ".local-browsers",
        pkg_root / "playwright" / ".local-browsers",
    ]
    for root in local_browser_roots:
        if not root.exists():
            continue
        for pattern in patterns:
            matches = sorted(root.glob(pattern))
            if matches:
                return str(matches[-1])

    return None


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
    render_mode = bool(os.getenv("RENDER") or os.getenv("RENDER_EXTERNAL_URL"))
    elements = build_50_elements(theme)[:element_limit]
    total = len(elements)
    rows: list[dict] = []

    if progress_callback:
        progress_callback("starting", 0, total, "")

    launch_kwargs = {"headless": True}
    if render_mode:
        launch_kwargs["args"] = [
            "--disable-dev-shm-usage",
            "--no-zygote",
            "--disable-gpu",
            "--single-process",
        ]
        launch_kwargs["chromium_sandbox"] = False
    fallback_executable = _resolve_chromium_executable()
    if fallback_executable:
        launch_kwargs["executable_path"] = fallback_executable

    async with async_playwright() as pw:
        if progress_callback:
            progress_callback("starting", 0, total, "launching_browser")

        browser = await asyncio.wait_for(pw.chromium.launch(**launch_kwargs), timeout=45)
        context = await asyncio.wait_for(browser.new_context(), timeout=20)
        if render_mode:
            # Reduce memory usage on free-tier containers.
            await context.route(
                "**/*",
                lambda route, request: route.abort()
                if request.resource_type in {"image", "media", "font", "stylesheet"}
                else route.continue_(),
            )

        if progress_callback:
            progress_callback("collecting", 0, total, "")

        semaphore = asyncio.Semaphore(1 if render_mode else 2)
        done = 0

        async def worker(element: str):
            nonlocal done
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        _collect_for_element(context, theme, element, per_element_limit),
                        timeout=95,
                    )
                except Exception:
                    # Timeout or site-level blocking should not freeze the entire batch.
                    result = (element, [], f"{theme} {element} c4d 3d icon")
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
