from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from app.tools.sandbox import sandbox_tools

CONFIG_DIR = Path(__file__).parent / "config"


def load_team() -> list[dict[str, str]]:
    config = yaml.safe_load((CONFIG_DIR / "agents.yaml").read_text(encoding="utf-8"))
    return [{"key": key, "role": value["role"].strip()} for key, value in config.items()]


@CrewBase
class EngineeringTeam:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(
        self,
        step_callback: Callable[[Any], None] | None = None,
        task_callback: Callable[[Any], None] | None = None,
    ) -> None:
        self.step_callback = step_callback
        self.task_callback = task_callback

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(config=self.agents_config["engineering_lead"], verbose=True)

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(config=self.agents_config["backend_engineer"], tools=sandbox_tools, verbose=True)

    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config["design_task"])

    @task
    def code_task(self) -> Task:
        return Task(config=self.tasks_config["code_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            step_callback=self.step_callback,
            task_callback=self.task_callback,
            verbose=True,
        )
