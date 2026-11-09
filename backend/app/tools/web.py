import atexit
import os
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path, PurePosixPath

from crewai.tools import tool

from app.runs import emit
from app.tools.sandbox import clean_env

BACKEND_DIR = Path(__file__).resolve().parents[2]
WEB_DIR = BACKEND_DIR / "web"
SRC_DIR = WEB_DIR / "src"
TEMPLATE_SRC = BACKEND_DIR / "template" / "src"
PREVIEW_PORT = 3100
PREVIEW_URL = f"http://localhost:{PREVIEW_PORT}"
ALLOWED_SUFFIXES = {".ts", ".tsx", ".css"}
PLACEHOLDER_TEXT = "Your app will appear here"
TYPECHECK_TIMEOUT_SECONDS = 120
PAGE_TIMEOUT_SECONDS = 90
STARTUP_TIMEOUT_SECONDS = 90
ERROR_MARKERS = ("⨯", "Failed to compile", "Module not found", "Error:", "SyntaxError", "Unhandled")


class WebSetupError(RuntimeError):
    pass


def _tool_path(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise WebSetupError(f"`{name}` was not found. Install Node.js 20 or newer to enable the frontend preview.")
    return path


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def ensure_dependencies() -> None:
    if (WEB_DIR / "node_modules").is_dir():
        return
    result = subprocess.run(
        [_tool_path("npm"), "install", "--no-audit", "--no-fund"],
        cwd=WEB_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=clean_env(),
    )
    if result.returncode != 0:
        raise WebSetupError(f"`npm install` failed in backend/web:\n{result.stderr[-1200:]}")


def reset_web_src() -> None:
    shutil.rmtree(SRC_DIR, ignore_errors=True)
    shutil.copytree(TEMPLATE_SRC, SRC_DIR)


def display_name(path: str) -> str | None:
    target = resolve_source(path)
    return None if target is None else f"web/{target.relative_to(WEB_DIR).as_posix()}"


def list_source_files() -> list[str]:
    if not SRC_DIR.exists():
        return []
    return sorted(p.relative_to(WEB_DIR).as_posix() for p in SRC_DIR.rglob("*") if p.is_file())


def resolve_source(path: str) -> Path | None:
    normalized = PurePosixPath(path.strip().replace("\\", "/"))
    parts = [part for part in normalized.parts if part not in ("", ".")]
    if parts and parts[0] == "src":
        parts = parts[1:]
    if not parts or normalized.is_absolute() or ".." in parts or Path(parts[-1]).suffix not in ALLOWED_SUFFIXES:
        return None
    return SRC_DIR.joinpath(*parts)


class PreviewServer:
    def __init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._lines: deque[str] = deque(maxlen=300)
        self._cursor = 0
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self) -> None:
        self.stop()
        if port_in_use(PREVIEW_PORT):
            raise WebSetupError(f"Port {PREVIEW_PORT} is already in use. Stop whatever is using it and try again.")
        shutil.rmtree(WEB_DIR / ".next", ignore_errors=True)
        with self._lock:
            self._lines.clear()
            self._cursor = 0
        env = {**clean_env(), "NEXT_TELEMETRY_DISABLED": "1"}
        self._process = subprocess.Popen(
            [_tool_path("node"), str(WEB_DIR / "node_modules" / "next" / "dist" / "bin" / "next"), "dev", "-p", str(PREVIEW_PORT)],
            cwd=WEB_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            start_new_session=os.name != "nt",
        )
        threading.Thread(target=self._pump, args=(self._process,), daemon=True).start()

    def _pump(self, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            with self._lock:
                self._lines.append(line.rstrip())

    def stop(self) -> None:
        process, self._process = self._process, None
        if process is None or process.poll() is not None:
            return
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
        else:
            os.killpg(process.pid, 15)
        process.wait(timeout=10)

    def wait_until_ready(self, timeout: float = STARTUP_TIMEOUT_SECONDS) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and self.running:
            if fetch_page(timeout=5)[0] == 200:
                return True
            time.sleep(1)
        return False

    def recent_log(self, count: int = 8) -> str:
        with self._lock:
            return "\n".join(list(self._lines)[-count:])

    def new_log_lines(self) -> list[str]:
        with self._lock:
            lines = list(self._lines)[self._cursor :] if self._cursor < len(self._lines) else []
            self._cursor = len(self._lines)
        return lines


preview = PreviewServer()
atexit.register(preview.stop)


def fetch_page(timeout: float = PAGE_TIMEOUT_SECONDS) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(PREVIEW_URL, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, ""


def typecheck() -> tuple[bool, str]:
    compiler = WEB_DIR / "node_modules" / "typescript" / "bin" / "tsc"
    try:
        result = subprocess.run(
            [_tool_path("node"), str(compiler), "--noEmit", "-p", "."],
            cwd=WEB_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TYPECHECK_TIMEOUT_SECONDS,
            env=clean_env(),
        )
    except subprocess.TimeoutExpired:
        return False, f"Type check timed out after {TYPECHECK_TIMEOUT_SECONDS} seconds."
    return result.returncode == 0, (result.stdout + result.stderr).strip()[-3000:]


def check_web_app() -> tuple[bool, str]:
    if not preview.running:
        return False, "The preview server is not running."
    problems: list[str] = []

    types_ok, type_output = typecheck()
    if not types_ok:
        problems.append(f"TypeScript errors:\n{type_output}")

    status, body = fetch_page()
    log_errors = [line for line in preview.new_log_lines() if any(marker in line for marker in ERROR_MARKERS)]
    if status != 200:
        problems.append(f"The page failed to render (HTTP {status}).")
    elif PLACEHOLDER_TEXT in body:
        problems.append("src/app/page.tsx is still the starter placeholder. Replace it with the real app.")
    if log_errors:
        problems.append("Dev server errors:\n" + "\n".join(log_errors[-12:]))

    return (not problems), "\n\n".join(problems)


@tool("List Web Files")
def list_web_files() -> str:
    """List the source files in the Next.js project, as paths like src/app/page.tsx."""
    names = list_source_files()
    emit("tool", tool="list_files", detail=f"{len(names)} web files")
    return "\n".join(names) or "The project has no source files."


@tool("Read Web File")
def read_web_file(path: str) -> str:
    """Read a source file from the Next.js project. Args: path, e.g. "src/app/page.tsx"."""
    emit("tool", tool="read_file", detail=path)
    target = resolve_source(path)
    if target is None or not target.is_file():
        return f"No such file: {path}"
    return target.read_text(encoding="utf-8")


@tool("Write Web File")
def write_web_file(path: str, content: str) -> str:
    """Create or replace a source file in the Next.js project. Only .ts, .tsx and .css files under src/
    are allowed. Args: path, e.g. "src/components/task-list.tsx"; content: the complete file."""
    target = resolve_source(path)
    if target is None:
        return "Invalid path: use a .ts, .tsx or .css file under src/, for example src/app/page.tsx."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    emit("file", name=f"web/{target.relative_to(WEB_DIR).as_posix()}", size=len(content), content=content)
    return f"Wrote {len(content)} characters to {target.relative_to(WEB_DIR).as_posix()}."


@tool("Check Web App")
def check_web_app_tool() -> str:
    """Type-check the Next.js project and render the page in the live preview.
    Returns OK or the errors to fix. Run it after writing files and fix everything it reports."""
    emit("tool", tool="check_web_app", detail="typecheck and render")
    ok, report = check_web_app()
    emit("check", ok=ok, report=report[-1500:])
    return "OK" if ok else f"Issues to fix:\n{report}"


web_tools = [list_web_files, read_web_file, write_web_file, check_web_app_tool]

for _tool in web_tools:
    _tool.cache_function = lambda *_args, **_kwargs: False
