from __future__ import annotations

import asyncio
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .services.elements import build_50_elements
from .services.pipeline import generate_theme_excel

TEST_ELEMENT_COUNT = 10
TEST_IMAGES_PER_ELEMENT = 3


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Holiday Icon Reference Collector")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

JOBS: dict[str, dict] = {}
LOCK = threading.Lock()


class GenerateRequest(BaseModel):
    theme: str = Field(min_length=1, max_length=80)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


def _update_job(job_id: str, **kwargs):
    with LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(kwargs)


def _run_job(job_id: str, theme: str):
    def progress(stage: str, current: int, total: int, element: str):
        _update_job(
            job_id,
            stage=stage,
            current=current,
            total=total,
            element=element,
            message=f"{stage}: {current}/{total} {element}".strip(),
        )

    try:
        output_path = asyncio.run(
            generate_theme_excel(
                theme=theme,
                output_dir=OUTPUT_DIR,
                progress_callback=progress,
                per_element_limit=TEST_IMAGES_PER_ELEMENT,
                element_limit=TEST_ELEMENT_COUNT,
            )
        )
        _update_job(
            job_id,
            status="done",
            stage="finished",
            file_name=output_path.name,
            message="completed",
        )
    except Exception as exc:
        _update_job(job_id, status="failed", stage="failed", message=str(exc))


@app.post("/api/jobs")
def create_job(req: GenerateRequest):
    theme = req.theme.strip()
    if not theme:
        raise HTTPException(status_code=400, detail="theme is required")
    elements = build_50_elements(theme)[:TEST_ELEMENT_COUNT]

    job_id = uuid.uuid4().hex
    with LOCK:
        JOBS[job_id] = {
            "status": "running",
            "stage": "queued",
            "current": 0,
            "total": len(elements),
            "element": "",
            "file_name": "",
            "message": "queued",
            "theme": theme,
            "elements": elements,
        }

    t = threading.Thread(target=_run_job, args=(job_id, theme), daemon=True)
    t.start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    with LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/api/download/{job_id}")
def download(job_id: str):
    with LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail="job not completed")

    target = OUTPUT_DIR / job["file_name"]
    if not target.exists():
        raise HTTPException(status_code=404, detail="file missing")

    return FileResponse(
        target,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=target.name,
    )
