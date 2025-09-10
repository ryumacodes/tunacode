from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Agent definition."""

    name: str = Field(..., description="Agent name")
    system_prompt_path: Path = Field(..., description="System prompt path")
    tools: list[str] = Field(..., description="Tools")


def load_agent(agent_path: Path) -> Agent:
    with open(agent_path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    version = data.get("version", 1)
    if version != 1:
        raise ValueError(f"Unsupported agent version: {version}")

    agent = data.get("agent", {})
    return Agent(**agent)
