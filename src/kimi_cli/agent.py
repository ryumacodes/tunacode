import importlib
import inspect
import string
from pathlib import Path
from typing import Any

import yaml
from kosong.tooling import CallableTool, SimpleToolset, Toolset
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Agent definition."""

    name: str = Field(..., description="Agent name")
    system_prompt_path: Path = Field(..., description="System prompt path")
    system_prompt_args: dict[str, str] = Field(
        default_factory=dict, description="System prompt arguments"
    )
    tools: list[str] = Field(default_factory=list, description="Tools")


def load_agent(agent_path: Path) -> Agent:
    with open(agent_path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    version = data.get("version", 1)
    if version != 1:
        raise ValueError(f"Unsupported agent version: {version}")

    agent_data = data.get("agent", {})
    agent = Agent(**agent_data)
    agent.system_prompt_path = agent_path.parent.joinpath(agent.system_prompt_path)
    return agent


def load_agent_by_name(agent_name: str) -> Agent | None:
    agent_path = Path(__file__).parent / "agents" / agent_name / "agent.yaml"
    if not agent_path.is_file():
        return None
    return load_agent(agent_path)


def load_system_prompt(agent: Agent, builtin_args: dict[str, Any]) -> str:
    system_prompt = agent.system_prompt_path.read_text().strip()
    return string.Template(system_prompt).substitute(builtin_args, **agent.system_prompt_args)


def load_tools(
    agent: Agent, dependencies: dict[type[Any], Any] | None = None
) -> tuple[Toolset, list[str]]:
    toolset = SimpleToolset()
    bad_tools = []
    for tool_path in agent.tools:
        tool = _load_tool(tool_path, dependencies or {})
        if tool:
            toolset += tool
        else:
            bad_tools.append(tool_path)
    return toolset, bad_tools


def _load_tool(tool_path: str, dependencies: dict[type[Any], Any]) -> CallableTool | None:
    module_name, class_name = tool_path.rsplit(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    cls = getattr(module, class_name, None)
    if cls is None:
        return None
    args = []
    for param in inspect.signature(cls).parameters.values():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            # once we encounter a keyword-only parameter, we stop injecting dependencies
            break
        # all positional parameters should be dependencies to be injected
        if param.annotation not in dependencies:
            raise ValueError(f"Tool dependency not found: {param.annotation}")
        args.append(dependencies[param.annotation])
    return cls(*args)


def load_agents_md(work_dir: Path) -> str | None:
    paths = [
        work_dir / "AGENTS.md",
        work_dir / "agents.md",
    ]
    for path in paths:
        if path.is_file():
            return path.read_text().strip()
    return None
