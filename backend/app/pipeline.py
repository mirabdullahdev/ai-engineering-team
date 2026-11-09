import traceback
from pathlib import Path

from dotenv import load_dotenv

from app.crew import EngineeringTeam, load_task_order
from app.runs import Run
from app.tools.sandbox import SANDBOX_DIR, reset_sandbox, run_test_suite

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

TASK_ORDER = load_task_order()
SAVED_OUTPUTS = {"design_task": "design.md", "test_task": "test_summary.md"}
MAX_FIX_ATTEMPTS = 2
FIXER = "backend_engineer"


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
            run.emit("file", name=SAVED_OUTPUTS[task_name], size=len(raw))
        run.emit("task_done", agent=agent_key, summary=raw[:600])
        completed += 1
        if completed < len(TASK_ORDER):
            run.emit("task_start", agent=TASK_ORDER[completed][1])

    def on_fix_done(output) -> None:
        run.emit("task_done", agent=FIXER, summary=str(getattr(output, "raw", output))[:600])

    def verify() -> tuple[bool, str]:
        run.emit("tool", tool="run_tests", detail="unittest discover")
        code, output = run_test_suite()
        run.emit("exec", file="tests", code=code, output=output)
        return code == 0, output

    def used(result) -> int:
        usage = getattr(result, "token_usage", None)
        return getattr(usage, "total_tokens", 0) or 0

    try:
        reset_sandbox()
        run.emit("run_started")
        run.emit("task_start", agent=TASK_ORDER[0][1])
        team = EngineeringTeam(step_callback=on_step, task_callback=on_task_done)
        tokens += used(team.crew().kickoff(inputs={"requirements": requirements}))

        passed, failures = verify()
        for _ in range(MAX_FIX_ATTEMPTS):
            if passed:
                break
            run.emit("task_start", agent=FIXER)
            fixer = EngineeringTeam(step_callback=on_step, task_callback=on_fix_done)
            tokens += used(fixer.fix_crew().kickoff(inputs={"requirements": requirements, "failures": failures}))
            passed, failures = verify()

        run.emit("run_finished", tokens=tokens or None, tests_passed=passed)
    except Exception as exc:
        traceback.print_exc()
        run.emit("run_error", message=str(exc)[:1200])
    finally:
        run.finish()
