import importlib
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
    system_prompt_args: dict[str, str] = Field(..., description="System prompt arguments")
    tools: list[str] = Field(..., description="Tools")


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


def load_system_prompt(agent: Agent, builtin_args: dict[str, Any]) -> str:
    system_prompt = agent.system_prompt_path.read_text().strip()
    return string.Template(system_prompt).substitute(builtin_args, **agent.system_prompt_args)


def load_tools(agent: Agent) -> tuple[Toolset, list[str]]:
    toolset = SimpleToolset()
    bad_tools = []
    for tool_path in agent.tools:
        tool = _load_tool(tool_path)
        if tool:
            toolset += tool
        else:
            bad_tools.append(tool_path)
    return toolset, bad_tools


def _load_tool(tool_path: str, **tool_kwargs) -> CallableTool | None:
    module_name, class_name = tool_path.rsplit(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    cls = getattr(module, class_name, None)
    if cls is None:
        return None
    return cls(**tool_kwargs)


def load_agents_md(work_dir: Path) -> str | None:
    paths = [
        work_dir / "AGENTS.md",
        work_dir / "agents.md",
    ]
    for path in paths:
        if path.is_file():
            return path.read_text().strip()
    return None
