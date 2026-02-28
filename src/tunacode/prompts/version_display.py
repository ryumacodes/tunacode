"""Utility for displaying prompt versions.

Provides functions to display current prompt versions in a human-readable format.
"""

from __future__ import annotations

from pathlib import Path

from tunacode.prompts.versioning import (
    AgentPromptVersions,
    compute_agent_prompt_versions,
)
from tunacode.types.canonical import PromptVersion


def format_prompt_version(version: PromptVersion | None, indent: str = "  ") -> str:
    """Format a PromptVersion for display.

    Args:
        version: The PromptVersion to format, or None.
        indent: Indentation string for nested fields.

    Returns:
        Formatted string representation.
    """
    if version is None:
        return f"{indent}<not available>"

    return (
        f"{indent}path: {version.source_path}\n"
        f"{indent}hash: {version.content_hash[:16]}...\n"
        f"{indent}length: {version.length} chars\n"
        f"{indent}mtime: {version.mtime:.2f}"
    )


def display_prompt_versions(versions: AgentPromptVersions) -> str:
    """Display AgentPromptVersions in a human-readable format.

    Args:
        versions: The AgentPromptVersions to display.

    Returns:
        Formatted string representation.
    """
    lines: list[str] = [
        "Prompt Versions",
        "===============",
        "",
    ]

    if versions.system_prompt:
        lines.extend(
            [
                "System Prompt:",
                format_prompt_version(versions.system_prompt),
                "",
            ]
        )
    else:
        lines.extend(["System Prompt: <not loaded>", ""])

    if versions.tunacode_context:
        lines.extend(
            [
                "TunaCode Context:",
                format_prompt_version(versions.tunacode_context),
                "",
            ]
        )
    else:
        lines.extend(["TunaCode Context: <not loaded>", ""])

    if versions.tool_prompts:
        lines.append("Tool Prompts:")
        for tool_name in sorted(versions.tool_prompts.keys()):
            tool_version = versions.tool_prompts[tool_name]
            lines.append(f"  {tool_name}:")
            lines.append(format_prompt_version(tool_version, indent="    "))
            lines.append("")
    else:
        lines.extend(["Tool Prompts: <none>", ""])

    lines.extend(
        [
            "Fingerprint:",
            f"  {versions.fingerprint[:16]}...",
            "",
            f"Computed at: {versions.computed_at:.2f}",
        ]
    )

    return "\n".join(lines)


def get_current_prompt_versions(
    system_prompt_path: Path | str | None = None,
    tunacode_context_path: Path | str | None = None,
) -> AgentPromptVersions:
    """Get current prompt versions for the tunacode session.

    Args:
        system_prompt_path: Path to system prompt file. Uses default if None.
        tunacode_context_path: Path to tunacode context file. Uses default if None.

    Returns:
        AgentPromptVersions with current versions.
    """
    if system_prompt_path is None:
        system_prompt_path = (
            Path(__file__).parent.parent.parent.parent / "prompts" / "system_prompt.md"
        )

    if tunacode_context_path is None:
        tunacode_context_path = Path.cwd() / "AGENTS.md"

    return compute_agent_prompt_versions(
        system_prompt_path=system_prompt_path,
        tunacode_context_path=tunacode_context_path,
    )


def print_prompt_versions() -> None:
    """Print current prompt versions to stdout.

    This is a convenience function for CLI usage.
    """
    versions = get_current_prompt_versions()
    print(display_prompt_versions(versions))
