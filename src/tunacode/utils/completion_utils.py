"""Completion helpers used by the Textual editor."""

from __future__ import annotations

from pathlib import Path


def textual_complete_paths(prefix: str) -> list[str]:
    """Return path completions for @-style references."""
    base = Path(prefix).expanduser()
    search_root = base.parent if base.parent != Path(".") else Path.cwd()
    stem = base.name
    candidates: list[str] = []
    try:
        for entry in search_root.iterdir():
            if not entry.name.startswith(stem):
                continue
            if prefix.startswith("/"):
                candidate = str(entry)
            else:
                candidate = entry.name if search_root == Path.cwd() else str(entry)
            suffix = "/" if entry.is_dir() else ""
            candidates.append(candidate + suffix)
    except (FileNotFoundError, PermissionError):
        return []
    return sorted(candidates)


def replace_token(text: str, start: int, end: int, replacement: str) -> str:
    """Replace a token in text at the given position."""
    return text[:start] + replacement + text[end:]
