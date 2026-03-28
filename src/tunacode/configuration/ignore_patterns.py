"""Shared ignore defaults and helpers for filesystem filtering."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Final

import pathspec

from tunacode.constants import ENV_FILE

GITIGNORE_FILE_NAME: Final[str] = ".gitignore"
GITIGNORE_STYLE: Final[str] = "gitwildmatch"
TEXT_ENCODING: Final[str] = "utf-8"
GIT_DIR_PATTERN: Final[str] = ".git/"
WILDCARD_CHARS = ("*", "?", "[")
EMPTY_IGNORE_PATTERNS: Final[tuple[str, ...]] = ()

DEFAULT_IGNORE_PATTERNS: Final[tuple[str, ...]] = (
    GIT_DIR_PATTERN,
    ".hg/",
    ".svn/",
    ".bzr/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "node_modules/",
    "bower_components/",
    ".venv/",
    "venv/",
    "env/",
    ".env/",
    "build/",
    "dist/",
    "_build/",
    "target/",
    ".idea/",
    ".vscode/",
    ".vs/",
    "htmlcov/",
    ".coverage",
    ".tox/",
    ".eggs/",
    "*.egg-info/",
    ".bundle/",
    "vendor/",
    ".terraform/",
    ".serverless/",
    ".next/",
    ".nuxt/",
    "coverage/",
    "tmp/",
    "temp/",
    ".cache/",
    "cache/",
    "logs/",
    "bin/",
    "obj/",
    ".zig-cache/",
    "zig-out/",
    "coverage.xml",
    "*.cover",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.swp",
    "*.swo",
    ".DS_Store",
    "Thumbs.db",
    ENV_FILE,
)


def _is_literal_dir_pattern(pattern: str) -> bool:
    return pattern.endswith("/") and not any(char in pattern for char in WILDCARD_CHARS)


def _extract_exclude_dirs(patterns: Iterable[str]) -> frozenset[str]:
    return frozenset(
        pattern.rstrip("/") for pattern in patterns if _is_literal_dir_pattern(pattern)
    )


DEFAULT_EXCLUDE_DIRS: Final[frozenset[str]] = _extract_exclude_dirs(DEFAULT_IGNORE_PATTERNS)


def normalize_ignore_patterns(patterns: Iterable[str]) -> tuple[str, ...]:
    """Drop empty patterns while preserving order."""
    return tuple(pattern for pattern in patterns if pattern)


def merge_ignore_patterns(
    base_patterns: Iterable[str],
    extra_patterns: Iterable[str],
) -> tuple[str, ...]:
    """Append extra patterns onto a base pattern set."""
    return tuple(base_patterns) + normalize_ignore_patterns(extra_patterns)


def read_ignore_file_lines(filepath: Path) -> tuple[str, ...]:
    """Read raw ignore-file lines, returning an empty tuple when unreadable."""
    try:
        ignore_text = filepath.read_text(encoding=TEXT_ENCODING)
    except (OSError, UnicodeDecodeError):
        return EMPTY_IGNORE_PATTERNS
    return tuple(ignore_text.splitlines())


def compile_ignore_spec(patterns: Iterable[str]) -> pathspec.PathSpec:
    """Compile gitignore-style patterns into a reusable matcher."""
    return pathspec.PathSpec.from_lines(GITIGNORE_STYLE, patterns)
