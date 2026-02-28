"""Prompt version computation and tracking.

Provides utilities for computing version identifiers for prompt files
based on content hash (SHA-256), modification time, and size.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

from tunacode.types.canonical import AgentPromptVersions, PromptVersion


def compute_prompt_version(source_path: Path | str) -> PromptVersion | None:
    """Compute a version identifier for a prompt file.

    Args:
        source_path: Path to the prompt file.

    Returns:
        PromptVersion with content hash, mtime, and length, or None if file doesn't exist.

    Examples:
        >>> version = compute_prompt_version("prompts/system_prompt.md")
        >>> version.content_hash  # doctest: +SKIP
        'a1b2c3d4...'
    """
    path = Path(source_path) if not isinstance(source_path, Path) else source_path

    if not path.exists():
        return None

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    mtime = os.path.getmtime(path)
    computed_at = time.time()
    length = len(content)

    return PromptVersion(
        source_path=str(path),
        content_hash=content_hash,
        mtime=mtime,
        computed_at=computed_at,
        length=length,
    )


def compute_agent_prompt_versions(
    system_prompt_path: Path | str | None = None,
    tunacode_context_path: Path | str | None = None,
    tool_prompt_paths: dict[str, Path | str] | None = None,
) -> AgentPromptVersions:
    """Compute combined version report for all prompts used by an agent.

    Aggregates versions for system prompt, tunacode context, and tool prompts.
    The fingerprint is a combined hash of all individual version hashes.

    Args:
        system_prompt_path: Path to system prompt file.
        tunacode_context_path: Path to tunacode context file (e.g., AGENTS.md).
        tool_prompt_paths: Mapping of tool name to prompt file path.

    Returns:
        AgentPromptVersions with individual versions and combined fingerprint.

    Examples:
        >>> versions = compute_agent_prompt_versions(
        ...     system_prompt_path="prompts/system_prompt.md",
        ...     tunacode_context_path="AGENTS.md",
        ...     tool_prompt_paths={"bash": "tools/prompts/bash.xml"},
        ... )
        >>> versions.fingerprint  # doctest: +SKIP
        'combined_hash...'
    """
    system_version = compute_prompt_version(system_prompt_path) if system_prompt_path else None
    context_version = (
        compute_prompt_version(tunacode_context_path) if tunacode_context_path else None
    )

    tool_versions: dict[str, PromptVersion] = {}
    if tool_prompt_paths:
        for tool_name, tool_path in tool_prompt_paths.items():
            version = compute_prompt_version(tool_path)
            if version is not None:
                tool_versions[tool_name] = version

    # Compute fingerprint from all version hashes
    fingerprint_parts: list[str] = []
    if system_version:
        fingerprint_parts.append(f"system:{system_version.content_hash}")
    if context_version:
        fingerprint_parts.append(f"context:{context_version.content_hash}")
    for tool_name in sorted(tool_versions.keys()):
        tool_version = tool_versions[tool_name]
        fingerprint_parts.append(f"{tool_name}:{tool_version.content_hash}")

    fingerprint_input = "|".join(fingerprint_parts)
    fingerprint = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
    computed_at = time.time()

    return AgentPromptVersions(
        system_prompt=system_version,
        tunacode_context=context_version,
        tool_prompts=tool_versions,
        fingerprint=fingerprint,
        computed_at=computed_at,
    )


def versions_equal(v1: PromptVersion | None, v2: PromptVersion | None) -> bool:
    """Compare two PromptVersion instances for equality.

    None values are considered equal only if both are None.

    Args:
        v1: First PromptVersion or None.
        v2: Second PromptVersion or None.

    Returns:
        True if versions are equal (same content hash), False otherwise.
    """
    if v1 is None and v2 is None:
        return True
    if v1 is None or v2 is None:
        return False
    return v1.content_hash == v2.content_hash


def agent_versions_equal(
    v1: AgentPromptVersions | None,
    v2: AgentPromptVersions | None,
) -> bool:
    """Compare two AgentPromptVersions instances for equality.

    None values are considered equal only if both are None.

    Args:
        v1: First AgentPromptVersions or None.
        v2: Second AgentPromptVersions or None.

    Returns:
        True if fingerprints are equal, False otherwise.
    """
    if v1 is None and v2 is None:
        return True
    if v1 is None or v2 is None:
        return False
    return v1.fingerprint == v2.fingerprint


__all__ = [
    "compute_prompt_version",
    "compute_agent_prompt_versions",
    "versions_equal",
    "agent_versions_equal",
]
