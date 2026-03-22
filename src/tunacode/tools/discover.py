"""Native tinyagent discover tool."""

from __future__ import annotations

import asyncio

from tinyagent.agent_types import (
    AgentTool,
    AgentToolResult,
    AgentToolUpdateCallback,
    JsonObject,
    TextContent,
)

from tunacode.exceptions import ToolExecutionError, ToolRetryError, UserAbortError

from tunacode.tools.utils.discover_pipeline import _discover_sync

_DISCOVER_DESCRIPTION = """Find and map code related to a concept, feature, or module.

Describe what you're looking for in natural language. Returns a structured
report of relevant files, their roles, key symbols, and relationships.
Use instead of manually chaining glob, grep, and read.
"""

_DISCOVER_PARAMETERS: JsonObject = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "query": {
            "type": "string",
            "description": "What to find, for example where auth is handled.",
        },
        "directory": {
            "type": "string",
            "description": "Project root to search from. Defaults to current directory.",
        },
    },
    "required": ["query"],
}


def _text_result(text: str) -> AgentToolResult:
    return AgentToolResult(content=[TextContent(text=text)], details={})


async def _run_discover(query: str, directory: str = ".") -> str:
    report = await asyncio.to_thread(_discover_sync, query, directory)
    return report.to_context()


async def _execute_discover(
    tool_call_id: str,
    args: JsonObject,
    signal: asyncio.Event | None,
    on_update: AgentToolUpdateCallback,
) -> AgentToolResult:
    _ = (tool_call_id, on_update)
    if signal is not None and signal.is_set():
        raise UserAbortError("Tool execution aborted: discover")

    query = args.get("query")
    directory = args.get("directory", ".")
    if not isinstance(query, str):
        raise ToolRetryError("Invalid arguments for tool 'discover': 'query' must be a string.")
    if not isinstance(directory, str):
        raise ToolRetryError(
            "Invalid arguments for tool 'discover': 'directory' must be a string."
        )

    try:
        result = await _run_discover(query=query, directory=directory)
    except (ToolRetryError, ToolExecutionError):
        raise
    except Exception as exc:  # noqa: BLE001
        raise ToolExecutionError(
            tool_name="discover",
            message=str(exc),
            original_error=exc,
        ) from exc

    return _text_result(result)


discover = AgentTool(
    name="discover",
    label="discover",
    description=_DISCOVER_DESCRIPTION,
    parameters=_DISCOVER_PARAMETERS,
    execute=_execute_discover,
)
