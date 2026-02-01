#!/usr/bin/env python3
"""Generate docs/codebase-map/structure/tree-structure.txt from src/tunacode."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "src" / "tunacode"
OUTPUT_PATH = REPO_ROOT / "docs" / "codebase-map" / "structure" / "tree-structure.txt"

EXCLUDED_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}

TREE_TITLE = "TunaCode Source Code Structure Tree"
TREE_UNDERLINE = "=" * len(TREE_TITLE)


@dataclass(frozen=True)
class TreeEntry:
    name: str
    is_dir: bool


def _iter_tree_entries(path: Path) -> list[TreeEntry]:
    entries: list[TreeEntry] = []
    for entry in sorted(path.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
        if entry.name in EXCLUDED_NAMES:
            continue
        if entry.suffix in EXCLUDED_SUFFIXES:
            continue
        entries.append(TreeEntry(name=entry.name, is_dir=entry.is_dir()))
    return entries


def _render_tree(path: Path, prefix: str) -> list[str]:
    lines: list[str] = []
    entries = _iter_tree_entries(path)
    for index, entry in enumerate(entries):
        is_last = index == len(entries) - 1
        connector = "└──" if is_last else "├──"
        suffix = "/" if entry.is_dir else ""
        lines.append(f"{prefix}{connector} {entry.name}{suffix}")

        if entry.is_dir:
            child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
            lines.extend(_render_tree(path / entry.name, child_prefix))
    return lines


def _render_header() -> list[str]:
    today = date.today().isoformat()
    source_label = f"<repo_root>/{SOURCE_DIR.relative_to(REPO_ROOT).as_posix()}"
    output_label = f"<repo_root>/{OUTPUT_PATH.relative_to(REPO_ROOT).as_posix()}"
    return [
        TREE_TITLE,
        TREE_UNDERLINE,
        "",
        f"Generated: {today}",
        f"Source: {source_label}",
        f"Output: {output_label}",
        "",
    ]


def _write_tree() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Missing source directory: {SOURCE_DIR}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    root_label = f"{SOURCE_DIR.relative_to(REPO_ROOT).as_posix()}/"
    lines = _render_header()
    lines.append(root_label)
    lines.extend(_render_tree(SOURCE_DIR, ""))
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    _write_tree()


if __name__ == "__main__":
    main()
