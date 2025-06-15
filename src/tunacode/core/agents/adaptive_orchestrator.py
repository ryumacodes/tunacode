"""
Adaptive orchestrator for architect mode.

Implements the hybrid approach with deterministic analysis, constrained planning,
parallel execution, and feedback loops.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...types import AgentRun, ModelName, ResponseState
from ..analysis import (Confidence, ConstrainedPlanner, FeedbackDecision, FeedbackLoop,
                        RequestAnalyzer)
from ..state import StateManager
from . import main as agent_main
from .readonly import ReadOnlyAgent


@dataclass
class ExecutionResult:
    """Result of executing a task."""

    task: Dict[str, Any]
    result: Any
    duration: float
    error: Optional[Exception] = None


class AdaptiveOrchestrator:
    """Orchestrates task execution with adaptive planning and parallel execution."""

    def __init__(self, state_manager: StateManager):
        self.state = state_manager
        self.analyzer = RequestAnalyzer()
        self.planner = ConstrainedPlanner(state_manager)
        self.feedback_loop = FeedbackLoop(state_manager)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Timeouts
        self.task_timeout = 30  # 30s per task
        self.total_timeout = 120  # 2min total

    async def run(self, request: str, model: ModelName | None = None) -> List[AgentRun]:
        """Execute a request with adaptive planning and feedback loops."""
        from rich.console import Console

        console = Console()

        model = model or self.state.session.current_model
        start_time = time.time()

        console.print("\n[cyan]Adaptive Orchestrator: Analyzing request...[/cyan]")

        try:
            # Step 1: Analyze the request
            intent = self.analyzer.analyze(request)
            console.print(
                f"[dim]Request type: {intent.request_type.value}, Confidence: {intent.confidence.name}[/dim]"
            )

            # Step 2: Generate initial task plan
            tasks = await self._get_initial_tasks(request, intent, model)
            if not tasks:
                console.print("[yellow]No tasks generated. Falling back to regular mode.[/yellow]")
                return []

            console.print(f"\n[cyan]Executing plan with {len(tasks)} initial tasks...[/cyan]")

            # Step 3: Execute with feedback loop
            return await self._execute_with_feedback(request, tasks, model, start_time)

        except asyncio.TimeoutError:
            console.print("[red]Orchestrator timeout. Falling back to regular mode.[/red]")
            return []
        except Exception as e:
            console.print(f"[red]Orchestrator error: {str(e)}. Falling back to regular mode.[/red]")
            return []

    async def _get_initial_tasks(
        self, request: str, intent: Any, model: ModelName
    ) -> Optional[List[Dict[str, Any]]]:
        """Get initial tasks either from analyzer or planner."""
        from rich.console import Console

        console = Console()

        # Try deterministic planning first
        if intent.confidence.value >= Confidence.MEDIUM.value:
            tasks = self.analyzer.generate_simple_tasks(intent)
            if tasks:
                console.print(f"[dim]Generated {len(tasks)} tasks deterministically[/dim]")
                return tasks

        # Fall back to LLM planning
        console.print("[dim]Using LLM planner for complex request[/dim]")
        try:
            task_objects = await self.planner.plan(request, model)
            # Convert Task objects to dicts
            return [
                {
                    "id": t.id,
                    "description": t.description,
                    "mutate": t.mutate,
                    "tool": t.tool,
                    "args": t.args,
                }
                for t in task_objects
            ]
        except Exception as e:
            console.print(f"[yellow]Planning failed: {str(e)}[/yellow]")
            return None

    async def _execute_with_feedback(
        self, request: str, initial_tasks: List[Dict[str, Any]], model: ModelName, start_time: float
    ) -> List[AgentRun]:
        """Execute tasks with feedback loop."""
        from rich.console import Console

        console = Console()

        all_results = []
        completed_tasks = []
        remaining_tasks = initial_tasks
        iteration = 0

        response_state = ResponseState()

        while remaining_tasks and iteration < self.feedback_loop.max_iterations:
            # Check total timeout
            if time.time() - start_time > self.total_timeout:
                console.print("[yellow]Total execution timeout reached[/yellow]")
                break

            console.print(
                f"\n[dim]Iteration {iteration + 1}: Executing {len(remaining_tasks)} tasks[/dim]"
            )

            # Execute current batch
            batch_results = await self._execute_task_batch(remaining_tasks, model)

            # Convert ExecutionResults to AgentRuns and collect
            for exec_result in batch_results:
                if exec_result.error:
                    console.print(f"[red]Task failed: {exec_result.task['description']}[/red]")
                    console.print(f"[red]Error: {str(exec_result.error)}[/red]")

                # Add to results
                all_results.append(exec_result.result)
                completed_tasks.append(exec_result.task)

                # Update response state
                if hasattr(exec_result.result, "result") and exec_result.result.result:
                    if (
                        hasattr(exec_result.result.result, "output")
                        and exec_result.result.result.output
                    ):
                        response_state.has_user_response = True

            # Analyze results and decide next steps
            feedback = await self.feedback_loop.analyze_results(
                request, completed_tasks, batch_results, iteration + 1, model
            )

            console.print(f"[dim]Feedback: {feedback.decision.value} - {feedback.summary}[/dim]")

            if feedback.decision == FeedbackDecision.COMPLETE:
                break
            elif feedback.decision == FeedbackDecision.ERROR:
                console.print(f"[red]Stopping due to error: {feedback.error_message}[/red]")
                break
            elif feedback.decision in [FeedbackDecision.CONTINUE, FeedbackDecision.RETRY]:
                if feedback.new_tasks:
                    remaining_tasks = feedback.new_tasks
                    console.print(f"[dim]Generated {len(remaining_tasks)} follow-up tasks[/dim]")
                else:
                    console.print("[yellow]No new tasks generated. Stopping.[/yellow]")
                    break

            iteration += 1

        console.print(
            f"\n[green]Adaptive execution completed after {iteration + 1} iterations[/green]"
        )

        # Add final summary if needed
        if not response_state.has_user_response and all_results:
            # Create a summary of what was done
            summary_parts = [f"Completed {len(completed_tasks)} tasks:"]
            for task in completed_tasks[:5]:  # Show first 5
                summary_parts.append(f"• {task['description']}")
            if len(completed_tasks) > 5:
                summary_parts.append(f"• ... and {len(completed_tasks) - 5} more")

            class SummaryResult:
                def __init__(self, output: str):
                    self.output = output

            class SummaryRun:
                def __init__(self, output: str):
                    self.result = SummaryResult(output)

            all_results.append(SummaryRun("\n".join(summary_parts)))

        return all_results

    async def _execute_task_batch(
        self, tasks: List[Dict[str, Any]], model: ModelName
    ) -> List[ExecutionResult]:
        """Execute a batch of tasks with parallelization."""
        from rich.console import Console

        console = Console()

        # Separate read and write tasks
        read_tasks = [t for t in tasks if not t.get("mutate", False)]
        write_tasks = [t for t in tasks if t.get("mutate", False)]

        results = []

        # Execute read tasks in parallel
        if read_tasks:
            if len(read_tasks) > 1:
                console.print(f"[dim]Executing {len(read_tasks)} read tasks in parallel...[/dim]")

            read_coros = [self._execute_single_task(task, model) for task in read_tasks]
            read_results = await asyncio.gather(*read_coros, return_exceptions=True)

            for task, result in zip(read_tasks, read_results):
                if isinstance(result, Exception):
                    results.append(
                        ExecutionResult(task=task, result=None, duration=0, error=result)
                    )
                else:
                    results.append(result)

        # Execute write tasks sequentially
        for task in write_tasks:
            console.print(f"[dim]Executing write task: {task['description']}[/dim]")
            try:
                result = await self._execute_single_task(task, model)
                results.append(result)
            except Exception as e:
                results.append(ExecutionResult(task=task, result=None, duration=0, error=e))

        return results

    async def _execute_single_task(self, task: Dict[str, Any], model: ModelName) -> ExecutionResult:
        """Execute a single task."""
        start_time = time.time()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(self._run_task(task, model), timeout=self.task_timeout)

            duration = time.time() - start_time
            return ExecutionResult(task=task, result=result, duration=duration)

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return ExecutionResult(
                task=task,
                result=None,
                duration=duration,
                error=Exception(f"Task timed out after {self.task_timeout}s"),
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(task=task, result=None, duration=duration, error=e)

    async def _run_task(self, task: Dict[str, Any], model: ModelName) -> AgentRun:
        """Run a task using the appropriate agent."""
        from rich.console import Console

        console = Console()

        # Show task execution
        task_type = "WRITE" if task.get("mutate", False) else "READ"
        console.print(f"\n[dim][Task {task['id']}] {task_type}[/dim]")
        console.print(f"[dim]  → {task['description']}[/dim]")

        # If task has specific tool and args, format the request
        if task.get("tool") and task.get("args"):
            # This is a specific tool call
            tool_request = self._format_tool_request(task)
        else:
            # This is a general request
            tool_request = task["description"]

        # Execute using appropriate agent
        if task.get("mutate", False):
            agent_main.get_or_create_agent(model, self.state)
            result = await agent_main.process_request(model, tool_request, self.state)
        else:
            agent = ReadOnlyAgent(model, self.state)
            result = await agent.process_request(tool_request)

        console.print(f"[dim][Task {task['id']}] Complete[/dim]")
        return result

    def _format_tool_request(self, task: Dict[str, Any]) -> str:
        """Format a specific tool request."""
        tool = task["tool"]
        args = task["args"]

        # Format based on tool type
        if tool == "read_file":
            return f"Read the file {args.get('file_path', '')}"
        elif tool == "grep":
            pattern = args.get("pattern", "")
            directory = args.get("directory", ".")
            return f"Search for '{pattern}' in {directory}"
        elif tool == "write_file":
            return f"Create file {args.get('file_path', '')} with appropriate content"
        elif tool == "update_file":
            return f"Update {args.get('file_path', '')} as needed"
        elif tool == "run_command":
            return f"Run command: {args.get('command', '')}"
        elif tool == "bash":
            return f"Execute bash command: {args.get('command', '')}"
        else:
            return task["description"]
