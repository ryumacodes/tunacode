"""Agent orchestration scaffolding.

This module defines an ``OrchestratorAgent`` class that demonstrates how
higher level planning and delegation could be layered on top of the existing
``process_request`` workflow.  The goal is to keep orchestration logic isolated
from the core agent implementation while reusing all current tooling and state
handling provided by ``main.process_request``.
"""

from __future__ import annotations

import asyncio
import itertools
from typing import List

from ...types import AgentRun, ModelName
from ..llm.planner import make_plan
from ..state import StateManager
from . import main as agent_main
from .planner_schema import Task
from .readonly import ReadOnlyAgent


class OrchestratorAgent:
    """Plan and run a sequence of sub-agent tasks."""

    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    async def plan(self, request: str, model: ModelName) -> List[Task]:
        """Plan tasks for a user request using the planner LLM."""

        return await make_plan(request, model, self.state)

    async def _run_sub_task(self, task: Task, model: ModelName) -> AgentRun:
        """Execute a single task using an appropriate sub-agent."""
        from rich.console import Console

        console = Console()

        # Show which task is being executed
        task_type = "✏️  WRITE" if task.mutate else "👁  READ"
        console.print(f"\n[dim][Executing Task {task.id}] {task_type}[/dim]")
        console.print(f"[dim]  → {task.description}[/dim]")

        if task.mutate:
            agent_main.get_or_create_agent(model, self.state)
            result = await agent_main.process_request(model, task.description, self.state)
        else:
            agent = ReadOnlyAgent(model, self.state)
            result = await agent.process_request(task.description)

        console.print(f"[dim][Task {task.id}] ✓ Complete[/dim]")
        return result

    async def run(self, request: str, model: ModelName | None = None) -> List[AgentRun]:
        """Plan and execute a user request.

        Parameters
        ----------
        request:
            The high level user request to process.
        model:
            Optional model name to use for sub agents.  Defaults to the current
            session model.
        """
        from rich.console import Console

        console = Console()
        model = model or self.state.session.current_model

        # Show orchestrator is starting
        console.print(
            "\n[cyan]🎯 Orchestrator Mode: Analyzing request and creating execution plan...[/cyan]"
        )

        tasks = await self.plan(request, model)

        # Show execution is starting
        console.print(f"\n[cyan]🚀 Executing plan with {len(tasks)} tasks...[/cyan]")

        results: List[AgentRun] = []
        for mutate_flag, group in itertools.groupby(tasks, key=lambda t: t.mutate):
            if mutate_flag:
                for t in group:
                    results.append(await self._run_sub_task(t, model))
            else:
                # Show parallel execution
                task_list = list(group)
                if len(task_list) > 1:
                    console.print(
                        f"\n[dim][Parallel Execution] Running {len(task_list)} read-only tasks concurrently...[/dim]"
                    )
                coros = [self._run_sub_task(t, model) for t in task_list]
                results.extend(await asyncio.gather(*coros))

        console.print("\n[green]✅ Orchestrator completed all tasks successfully![/green]")

        return results
