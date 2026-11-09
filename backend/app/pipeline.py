import threading
import traceback
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv

from app.crew import EngineeringTeam, load_task_order
from app.runs import Run
from app.streaming import install_streaming
from app.tools.sandbox import SANDBOX_DIR, reset_sandbox, run_test_suite
from app.tools.web import (
    PREVIEW_URL,
    WebSetupError,
    check_web_app,
    ensure_dependencies,
    preview,
    reset_web_src,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
install_streaming()

TASK_ORDER = load_task_order()
SAVED_OUTPUTS = {"design_task": "design.md", "test_task": "test_summary.md"}
MAX_FIX_ATTEMPTS = 2
BACKEND_FIXER = "backend_engineer"
FRONTEND_FIXER = "frontend_engineer"


def run_build(run: Run, requirements: str) -> None:
    completed = 0
    tokens = 0

    def on_step(step) -> None:
        text = str(getattr(step, "thought", None) or getattr(step, "text", None) or "").strip()
        if text:
            run.emit("thought", text=text[:600])

    def on_task_done(output) -> None:
        nonlocal completed
        task_name, agent_key = TASK_ORDER[completed]
        raw = str(getattr(output, "raw", output))
        if task_name in SAVED_OUTPUTS:
            (SANDBOX_DIR / SAVED_OUTPUTS[task_name]).write_text(raw, encoding="utf-8")
            run.emit("file", name=SAVED_OUTPUTS[task_name], size=len(raw), content=raw)
        run.emit("task_done", agent=agent_key, summary=raw[:600])
        completed += 1
        if completed < len(TASK_ORDER):
            run.emit("task_start", agent=TASK_ORDER[completed][1])

    def fix_done(agent_key: str) -> Callable[[object], None]:
        return lambda output: run.emit("task_done", agent=agent_key, summary=str(getattr(output, "raw", output))[:600])

    def verify_backend() -> tuple[bool, str]:
        run.emit("tool", tool="run_tests", detail="unittest discover")
        code, output = run_test_suite()
        run.emit("exec", file="tests", code=code, output=output)
        return code == 0, output

    def verify_web() -> tuple[bool, str]:
        run.emit("tool", tool="check_web_app", detail="typecheck and render")
        ok, report = check_web_app()
        run.emit("check", ok=ok, report=report[-1500:])
        return ok, report

    def used(result) -> int:
        usage = getattr(result, "token_usage", None)
        return getattr(usage, "total_tokens", 0) or 0

    def announce_preview() -> None:
        if preview.wait_until_ready():
            run.emit("preview_ready", url=PREVIEW_URL)
        else:
            run.emit("tool", tool="setup", detail=f"the preview server did not start: {preview.recent_log()}")

    try:
        reset_sandbox()
        reset_web_src()
        run.emit("run_started")
        run.emit("tool", tool="setup", detail="preparing the frontend preview")
        ensure_dependencies()
        preview.start()
        threading.Thread(target=announce_preview, daemon=True).start()

        run.emit("task_start", agent=TASK_ORDER[0][1])
        team = EngineeringTeam(step_callback=on_step, task_callback=on_task_done)
        tokens += used(team.crew().kickoff(inputs={"requirements": requirements}))

        tests_passed, failures = verify_backend()
        for _ in range(MAX_FIX_ATTEMPTS):
            if tests_passed:
                break
            run.emit("task_start", agent=BACKEND_FIXER)
            fixer = EngineeringTeam(step_callback=on_step, task_callback=fix_done(BACKEND_FIXER))
            tokens += used(fixer.fix_crew().kickoff(inputs={"requirements": requirements, "failures": failures}))
            tests_passed, failures = verify_backend()

        web_ok, web_errors = verify_web()
        for _ in range(MAX_FIX_ATTEMPTS):
            if web_ok:
                break
            run.emit("task_start", agent=FRONTEND_FIXER)
            fixer = EngineeringTeam(step_callback=on_step, task_callback=fix_done(FRONTEND_FIXER))
            tokens += used(fixer.fix_web_crew().kickoff(inputs={"requirements": requirements, "web_errors": web_errors}))
            web_ok, web_errors = verify_web()

        run.emit("run_finished", tokens=tokens or None, tests_passed=tests_passed, web_ok=web_ok)
    except WebSetupError as exc:
        run.emit("run_error", message=str(exc))
    except Exception as exc:
        traceback.print_exc()
        run.emit("run_error", message=str(exc)[:1200])
    finally:
        run.finish()
