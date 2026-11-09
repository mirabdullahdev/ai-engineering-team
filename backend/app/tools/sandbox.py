import os
import shutil
import subprocess
import sys
from pathlib import Path

from crewai.tools import tool

from app.runs import emit

SANDBOX_DIR = Path(__file__).resolve().parents[2] / "sandbox"
EXEC_TIMEOUT_SECONDS = 120
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")
INTERPRETER = Path(sys.base_prefix) / ("python.exe" if os.name == "nt" else "bin/python")


def reset_sandbox() -> None:
    SANDBOX_DIR.mkdir(exist_ok=True)
    for entry in SANDBOX_DIR.iterdir():
        shutil.rmtree(entry) if entry.is_dir() else entry.unlink()


def clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not any(m in k.upper() for m in SECRET_MARKERS)}


def _execute(arguments: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            [str(INTERPRETER), "-E", "-s", "-X", "utf8", *arguments],
            cwd=SANDBOX_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=EXEC_TIMEOUT_SECONDS,
            env=clean_env(),
        )
    except subprocess.TimeoutExpired:
        return -1, "", f"Timed out after {EXEC_TIMEOUT_SECONDS} seconds."
    return result.returncode, result.stdout, result.stderr


def _combine(stdout: str, stderr: str) -> str:
    return "\n".join(part for part in (stdout, stderr) if part).strip()[-4000:]


def _resolve(filename: str) -> Path | None:
    if not filename or filename.startswith(".") or "/" in filename or "\\" in filename:
        return None
    return SANDBOX_DIR / filename


@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """List the filenames currently in the sandbox directory."""
    names = sorted(p.name for p in SANDBOX_DIR.iterdir() if p.is_file())
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
    emit("file", name=filename, size=len(content), content=content)
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """Run a Python file in the sandbox and return its exit code, stdout and stderr.
    Only the standard library is available. unittest reports results on stderr.
    Args: filename, e.g. "test_backend.py"."""
    path = _resolve(filename)
    if path is None or not path.is_file():
        return f"No such file in the sandbox: {filename}"
    emit("tool", tool="run_python", detail=filename)
    code, stdout, stderr = _execute([filename])
    emit("exec", file=filename, code=code, output=_combine(stdout, stderr))
    return f"Exit code: {code}\n\n--- stdout ---\n{stdout or '(empty)'}\n\n--- stderr ---\n{stderr or '(empty)'}"


def run_test_suite() -> tuple[int, str]:
    code, stdout, stderr = _execute(["-m", "unittest", "discover", "-p", "test*.py"])
    return code, _combine(stdout, stderr)


sandbox_tools = [list_sandbox_files, read_sandbox_file, write_sandbox_file, run_sandbox_python]

for _tool in sandbox_tools:
    _tool.cache_function = lambda *_args, **_kwargs: False
