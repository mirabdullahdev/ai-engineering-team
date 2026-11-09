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
from app.tools.sandbox import PROJECT_ENTRIES, SANDBOX_DIR

app = FastAPI(title="AI Engineering Team")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    requirements: str = Field(min_length=10, max_length=4000)


def _sandbox_files() -> list[str]:
    if not SANDBOX_DIR.exists():
        return []
    return sorted(p.name for p in SANDBOX_DIR.iterdir() if p.is_file() and p.name not in PROJECT_ENTRIES)


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


@app.get("/api/files")
def list_files() -> list[str]:
    return _sandbox_files()


@app.get("/api/files/{name}")
def read_file(name: str) -> Response:
    if name not in _sandbox_files():
        raise HTTPException(404, "No such file")
    return Response((SANDBOX_DIR / name).read_text(encoding="utf-8"), media_type="text/plain; charset=utf-8")


@app.get("/api/download")
def download() -> Response:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in _sandbox_files():
            archive.write(SANDBOX_DIR / name, name)
    return Response(
        buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="project.zip"'},
    )
