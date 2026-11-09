import io
import json
import threading
import zipfile

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.crew import load_team
from app.pipeline import run_build
from app.runs import Run, RunBusyError, create_run, get_run
from app.tools.sandbox import SANDBOX_DIR
from app.tools.web import PREVIEW_URL, WEB_DIR, list_source_files, preview

app = FastAPI(title="AI Engineering Team")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    requirements: str = Field(min_length=10, max_length=4000)


WEB_PREFIX = "web/"
WEB_PROJECT_FILES = ("package.json", "tsconfig.json", "next.config.ts", "postcss.config.js", "tailwind.config.js")


def _backend_files() -> list[str]:
    if not SANDBOX_DIR.exists():
        return []
    return sorted(p.name for p in SANDBOX_DIR.iterdir() if p.is_file())


def _all_files() -> list[str]:
    return _backend_files() + [WEB_PREFIX + name for name in list_source_files()]


def _run_or_404(run_id: str) -> Run:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(404, "Unknown run")
    return run


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/team")
def team() -> list[dict[str, str]]:
    return load_team()


@app.post("/api/runs")
def start_run(request: RunRequest) -> dict[str, str]:
    try:
        run = create_run()
    except RunBusyError as exc:
        raise HTTPException(409, str(exc)) from exc
    threading.Thread(target=run_build, args=(run, request.requirements), daemon=True).start()
    return {"run_id": run.id}


@app.get("/api/runs/{run_id}/events")
def stream_events(run_id: str) -> StreamingResponse:
    run = _run_or_404(run_id)

    def generate():
        index = 0
        while True:
            events, finished = run.wait_for(index)
            for event in events:
                yield f"data: {json.dumps(event)}\n\n"
            index += len(events)
            if finished:
                return
            if not events:
                yield ": keepalive\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/preview")
def preview_status() -> dict[str, str | bool]:
    return {"url": PREVIEW_URL, "running": preview.running}


@app.get("/api/files")
def list_files() -> list[str]:
    return _all_files()


@app.get("/api/files/{name:path}")
def read_file(name: str) -> Response:
    if name not in _all_files():
        raise HTTPException(404, "No such file")
    path = WEB_DIR / name.removeprefix(WEB_PREFIX) if name.startswith(WEB_PREFIX) else SANDBOX_DIR / name
    return Response(path.read_text(encoding="utf-8"), media_type="text/plain; charset=utf-8")


@app.get("/api/download")
def download() -> Response:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in _backend_files():
            archive.write(SANDBOX_DIR / name, f"backend/{name}")
        for name in list_source_files():
            archive.write(WEB_DIR / name, f"frontend/{name}")
        for name in WEB_PROJECT_FILES:
            archive.write(WEB_DIR / name, f"frontend/{name}")
    return Response(
        buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="project.zip"'},
    )
