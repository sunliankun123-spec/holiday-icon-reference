from __future__ import annotations

import imghdr
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment
import requests

PREVIEW_MAX_PX = 220
PREVIEW_COL_WIDTH = 34
PREVIEW_ROW_HEIGHT_PT = 170


def _fit_size(width: int, height: int, max_px: int) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        return max_px, max_px
    ratio = min(max_px / width, max_px / height, 1.0)
    return max(1, int(width * ratio)), max(1, int(height * ratio))


def _download_preview(url: str) -> str | None:
    if not url:
        return None
    try:
        resp = requests.get(
            url,
            timeout=(10, 20),
            allow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "").lower()
        if not content_type.startswith("image/"):
            return None

        raw = resp.content
        ext = imghdr.what(None, h=raw) or "jpg"
        if ext == "jpeg":
            ext = "jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        tmp.write(raw)
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception:
        return None


def write_excel(rows: Iterable[dict], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)

    wb = Workbook()
    ws = wb.active
    ws.title = "icon_references"
    ws.append(["theme", "element", "image_index", "search_query", "source", "image_preview"])

    temp_files: list[str] = []
    futures = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        for row_idx, row in enumerate(rows, start=2):
            ws.append(
                [
                    row["theme"],
                    row["element"],
                    row["image_index"],
                    row["search_query"],
                    row["source"],
                    "",
                ]
            )
            futures[executor.submit(_download_preview, row["image_url"])] = row_idx

        for future in as_completed(futures):
            row_idx = futures[future]
            temp_path = future.result()
            if not temp_path:
                continue
            temp_files.append(temp_path)
            img = XLImage(temp_path)
            img.width, img.height = _fit_size(img.width, img.height, PREVIEW_MAX_PX)
            ws.add_image(img, f"F{row_idx}")
            ws.row_dimensions[row_idx].height = PREVIEW_ROW_HEIGHT_PT

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 60
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = PREVIEW_COL_WIDTH
    ws.freeze_panes = "A2"

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=5):
        for cell in row:
            cell.alignment = center

    ws2 = wb.create_sheet(title="element_list")
    ws2.append(["theme", "element"])
    seen = set()
    for row in rows:
        key = (row["theme"], row["element"])
        if key in seen:
            continue
        seen.add(key)
        ws2.append([row["theme"], row["element"]])
    ws2.column_dimensions["A"].width = 20
    ws2.column_dimensions["B"].width = 30
    for row in ws2.iter_rows(min_row=1, max_row=ws2.max_row, min_col=1, max_col=2):
        for cell in row:
            cell.alignment = center

    wb.save(output_path)
    for temp_file in temp_files:
        try:
            Path(temp_file).unlink(missing_ok=True)
        except Exception:
            pass

    return output_path
