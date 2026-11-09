import os
import shutil
import subprocess
from pathlib import Path

from crewai.tools import tool

from app.runs import emit

SANDBOX_DIR = Path(__file__).resolve().parents[2] / "sandbox"
EXEC_TIMEOUT_SECONDS = 120
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")
ENV_BLOCKLIST = {"VIRTUAL_ENV"}
SANDBOX_PACKAGES = ["gradio", "pandas<3"]
PROJECT_ENTRIES = {"pyproject.toml", "uv.lock", ".venv"}


def reset_sandbox() -> None:
    SANDBOX_DIR.mkdir(exist_ok=True)
    if not (SANDBOX_DIR / "pyproject.toml").exists():
        subprocess.run(["uv", "init", "--bare", "--no-workspace", "--python", "3.12"], cwd=SANDBOX_DIR, check=True)
        subprocess.run(["uv", "add", *SANDBOX_PACKAGES], cwd=SANDBOX_DIR, check=True)
    for entry in SANDBOX_DIR.iterdir():
        if entry.name in PROJECT_ENTRIES:
            continue
        shutil.rmtree(entry) if entry.is_dir() else entry.unlink()


def _clean_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in ENV_BLOCKLIST and not any(marker in key.upper() for marker in SECRET_MARKERS)
    }


def _resolve(filename: str) -> Path | None:
    if not filename or filename.startswith(".") or "/" in filename or "\\" in filename:
        return None
    if filename in PROJECT_ENTRIES:
        return None
    return SANDBOX_DIR / filename


@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """List the filenames currently in the sandbox directory."""
    names = sorted(p.name for p in SANDBOX_DIR.iterdir() if p.is_file() and p.name not in PROJECT_ENTRIES)
    emit("tool", tool="list_files", detail=f"{len(names)} files")
    return "\n".join(names) or "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """Read a file from the sandbox. Args: filename, e.g. "backend.py"."""
    emit("tool", tool="read_file", detail=filename)
    path = _resolve(filename)
    if path is None or not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return path.read_text(encoding="utf-8")


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """Write text to a sandbox file, replacing it if it exists. Args: filename, content."""
    path = _resolve(filename)
    if path is None:
        return "Invalid filename: use a plain filename with no directories."
    path.write_text(content, encoding="utf-8")
    emit("file", name=filename, size=len(content))
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """Run a Python file in the sandbox and return its exit code, stdout and stderr.
    unittest reports results on stderr. Args: filename, e.g. "test_backend.py"."""
    path = _resolve(filename)
    if path is None or not path.is_file():
        return f"No such file in the sandbox: {filename}"
    emit("tool", tool="run_python", detail=filename)
    try:
        result = subprocess.run(
            ["uv", "run", "python", filename],
            cwd=SANDBOX_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=EXEC_TIMEOUT_SECONDS,
            env=_clean_env(),
        )
    except subprocess.TimeoutExpired:
        emit("exec", file=filename, code=-1, output=f"Timed out after {EXEC_TIMEOUT_SECONDS} seconds.")
        return f"Timed out after {EXEC_TIMEOUT_SECONDS} seconds."
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    emit("exec", file=filename, code=result.returncode, output=output[-4000:])
    return (
        f"Exit code: {result.returncode}\n\n"
        f"--- stdout ---\n{result.stdout or '(empty)'}\n\n"
        f"--- stderr ---\n{result.stderr or '(empty)'}"
    )


sandbox_tools = [list_sandbox_files, read_sandbox_file, write_sandbox_file, run_sandbox_python]

for _tool in sandbox_tools:
    _tool.cache_function = lambda *_args, **_kwargs: False
