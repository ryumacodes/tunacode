"""
Module: tunacode.core.agents.delegation_tools

Delegation tools for multi-agent workflows using pydantic-ai's delegation pattern.
"""

import json
from collections.abc import Awaitable, Callable
from typing import TypedDict, cast

from pydantic_ai import RunContext

from tunacode.types import SessionStateProtocol

from tunacode.core.agents.research_agent import create_research_agent

MAX_RESEARCH_FILES: int = 3


class ResearchCodeExample(TypedDict, total=False):
    file: str
    code: str
    explanation: str


class ResearchResult(TypedDict, total=False):
    relevant_files: list[str]
    key_findings: list[str]
    code_examples: list[ResearchCodeExample]
    recommendations: list[str]
    error: bool
    error_type: str
    error_message: str


def create_research_codebase_tool(
    session: SessionStateProtocol,
) -> Callable[[RunContext[None], str, list[str] | None, int], Awaitable[ResearchResult]]:
    """Factory to create research_codebase delegation tool with session closure.

    Args:
        session: Session state for current model and configuration.

    Returns:
        Async function that delegates research queries to specialized research agent

    Note:
        Progress callback is retrieved from session.tool_progress_callback
        at runtime to support dynamic callback updates without agent recreation.
    """

    async def research_codebase(
        ctx: RunContext[None],
        query: str,
        directories: list[str] | None = None,
        max_files: int = MAX_RESEARCH_FILES,
    ) -> ResearchResult:
        """Delegate codebase research to specialized read-only agent.

        This tool creates a child agent with read-only tools (grep, glob, list_dir, read_file)
        and delegates research queries to it. The child agent's usage is automatically
        aggregated with the parent agent's usage via ctx.usage.

        Args:
            ctx: RunContext with usage tracking (automatically passed by pydantic-ai)
            query: Research query describing what to find in the codebase
            directories: List of directories to search (defaults to ["."])
            max_files: Maximum number of files to analyze (hard limit enforced)

        Returns:
            Structured research findings dict with:
                - relevant_files: list of file paths discovered
                - key_findings: list of important discoveries
                - code_examples: relevant code snippets with explanations
                - recommendations: next steps or areas needing attention
        """
        # Enforce hard limit on max_files
        effective_max_files = min(max_files, MAX_RESEARCH_FILES)

        if directories is None:
            directories = ["."]

        # Get current model from session (same model as parent agent)
        model = session.current_model

        # Note: Research agent panel display is handled by orchestrator/orchestrator.py
        # which shows a purple panel with query details before execution

        # Get progress callback from session (set at request time by UI)
        progress_callback = session.tool_progress_callback

        research_agent = create_research_agent(
            model,
            session,
            max_files=effective_max_files,
            progress_callback=progress_callback,
        )

        # Construct research prompt
        directories_display = ", ".join(directories)
        prompt = f"""Research the codebase for: {query}

Search in directories: {directories_display}
Analyze up to {effective_max_files} most relevant files (hard limit enforced).

Return a structured summary with:
- relevant_files: list of file paths found
- key_findings: list of important discoveries
- code_examples: relevant code snippets with explanations
- recommendations: next steps or areas needing attention
"""

        # Delegate to research agent with usage propagation
        try:
            result = await research_agent.run(
                prompt,
                usage=ctx.usage,  # Share usage tracking with parent agent
            )

            # Parse JSON string response from research agent
            output_str = result.output
            try:
                parsed_raw = json.loads(output_str)
                if not isinstance(parsed_raw, dict):
                    raise TypeError("Research result must be a JSON object")
                parsed = cast(ResearchResult, parsed_raw)
                return parsed
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON, wrap the response in a structured format
                return {
                    "relevant_files": [],
                    "key_findings": [output_str],
                    "code_examples": [],
                    "recommendations": [],
                }

        except Exception as e:
            # Catch all delegation errors (validation failures, pydantic-ai errors, etc.)
            # Return structured error response instead of crashing
            return {
                "error": True,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "relevant_files": [],
                "key_findings": [f"Error during research: {str(e)}"],
                "code_examples": [],
                "recommendations": [
                    "The research agent encountered an error. "
                    "Try simplifying the query or reducing the scope."
                ],
            }

    return research_codebase
