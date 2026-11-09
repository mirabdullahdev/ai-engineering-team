from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from app.tools.sandbox import sandbox_tools
from app.tools.web import web_tools

CONFIG_DIR = Path(__file__).parent / "config"
FIX_TASK = "fix_task"
FIX_WEB_TASK = "fix_web_task"

Callback = Callable[[Any], None] | None


def load_team() -> list[dict[str, str]]:
    config = yaml.safe_load((CONFIG_DIR / "agents.yaml").read_text(encoding="utf-8"))
    return [{"key": key, "role": value["role"].strip()} for key, value in config.items()]


def load_task_order() -> list[tuple[str, str]]:
    config = yaml.safe_load((CONFIG_DIR / "tasks.yaml").read_text(encoding="utf-8"))
    return [(name, cfg["agent"]) for name, cfg in config.items() if name not in (FIX_TASK, FIX_WEB_TASK)]


@CrewBase
class EngineeringTeam:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, step_callback: Callback = None, task_callback: Callback = None) -> None:
        self.step_callback = step_callback
        self.task_callback = task_callback

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(config=self.agents_config["engineering_lead"], verbose=True)

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(config=self.agents_config["backend_engineer"], tools=sandbox_tools, verbose=True)

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(config=self.agents_config["frontend_engineer"], tools=web_tools, verbose=True)

    @agent
    def test_engineer(self) -> Agent:
        return Agent(config=self.agents_config["test_engineer"], tools=sandbox_tools, verbose=True)

    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config["design_task"])

    @task
    def code_task(self) -> Task:
        return Task(config=self.tasks_config["code_task"])

    @task
    def frontend_task(self) -> Task:
        return Task(config=self.tasks_config["frontend_task"])

    @task
    def test_task(self) -> Task:
        return Task(config=self.tasks_config["test_task"])

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

    def fix_crew(self) -> Crew:
        fix = self.tasks_config[FIX_TASK]
        engineer = self.backend_engineer()
        return Crew(
            agents=[engineer],
            tasks=[
                Task(
                    description=fix["description"],
                    expected_output=fix["expected_output"],
                    agent=engineer,
                )
            ],
            process=Process.sequential,
            step_callback=self.step_callback,
            task_callback=self.task_callback,
            verbose=True,
        )

    def fix_web_crew(self) -> Crew:
        fix = self.tasks_config[FIX_WEB_TASK]
        engineer = self.frontend_engineer()
        return Crew(
            agents=[engineer],
            tasks=[Task(description=fix["description"], expected_output=fix["expected_output"], agent=engineer)],
            process=Process.sequential,
            step_callback=self.step_callback,
            task_callback=self.task_callback,
            verbose=True,
        )
