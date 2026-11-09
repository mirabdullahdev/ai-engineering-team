import traceback
from pathlib import Path

import yaml
from dotenv import load_dotenv

from app.crew import CONFIG_DIR, EngineeringTeam
from app.runs import Run
from app.tools.sandbox import SANDBOX_DIR, reset_sandbox

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

TASK_ORDER: list[tuple[str, str]] = [
    (name, cfg["agent"])
    for name, cfg in yaml.safe_load((CONFIG_DIR / "tasks.yaml").read_text(encoding="utf-8")).items()
]
DESIGN_FILE = "design.md"


def run_build(run: Run, requirements: str) -> None:
    completed = 0

    def on_step(step) -> None:
        text = str(getattr(step, "thought", None) or getattr(step, "text", None) or "").strip()
        if text:
            run.emit("thought", text=text[:600])

    def on_task_done(output) -> None:
        nonlocal completed
        task_name, agent_key = TASK_ORDER[completed]
        raw = str(getattr(output, "raw", output))
        if task_name == "design_task":
            (SANDBOX_DIR / DESIGN_FILE).write_text(raw, encoding="utf-8")
            run.emit("file", name=DESIGN_FILE, size=len(raw))
        run.emit("task_done", agent=agent_key, summary=raw[:600])
        completed += 1
        if completed < len(TASK_ORDER):
            run.emit("task_start", agent=TASK_ORDER[completed][1])

    try:
        reset_sandbox()
        run.emit("run_started")
        run.emit("task_start", agent=TASK_ORDER[0][1])
        crew = EngineeringTeam(step_callback=on_step, task_callback=on_task_done).crew()
        result = crew.kickoff(inputs={"requirements": requirements})
        usage = getattr(result, "token_usage", None)
        run.emit("run_finished", tokens=getattr(usage, "total_tokens", None))
    except Exception as exc:
        traceback.print_exc()
        run.emit("run_error", message=str(exc)[:1200])
    finally:
        run.finish()
