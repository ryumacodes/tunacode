"""IgnoreManager implementation.

This module contains the ignore matching implementation without any caching.
Caching is handled by higher-level accessors (see infrastructure/cache).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

import pathspec

from tunacode.configuration.ignore_patterns import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_IGNORE_PATTERNS,
)

GITIGNORE_FILE_NAME = ".gitignore"
GITIGNORE_STYLE = "gitwildmatch"
PATH_SEPARATOR = "/"
MISSING_GITIGNORE_MTIME_NS = 0
EMPTY_PATTERNS: tuple[str, ...] = ()
TEXT_ENCODING = "utf-8"
ROOT_NOT_FOUND_ERROR = "Ignore root not found: {root}."
ROOT_NOT_DIRECTORY_ERROR = "Ignore root is not a directory: {root}."
PATH_OUTSIDE_ROOT_ERROR = "Path '{path}' is outside ignore root '{root}'."


def resolve_root(root: Path) -> Path:
    resolved_root = root.resolve()
    if not resolved_root.exists():
        message = ROOT_NOT_FOUND_ERROR.format(root=resolved_root)
        raise FileNotFoundError(message)
    if not resolved_root.is_dir():
        message = ROOT_NOT_DIRECTORY_ERROR.format(root=resolved_root)
        raise NotADirectoryError(message)
    return resolved_root


def build_gitignore_path(root: Path) -> Path:
    return root / GITIGNORE_FILE_NAME


def get_gitignore_mtime_ns(gitignore_path: Path) -> int:
    try:
        return gitignore_path.stat().st_mtime_ns
    except FileNotFoundError:
        return MISSING_GITIGNORE_MTIME_NS


def read_gitignore_lines(gitignore_path: Path) -> tuple[str, ...]:
    try:
        gitignore_text = gitignore_path.read_text(encoding=TEXT_ENCODING)
    except FileNotFoundError:
        return EMPTY_PATTERNS

    return tuple(gitignore_text.splitlines())


def build_patterns(gitignore_lines: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(DEFAULT_IGNORE_PATTERNS) + gitignore_lines


def compile_spec(patterns: tuple[str, ...]) -> pathspec.PathSpec:
    return pathspec.PathSpec.from_lines(GITIGNORE_STYLE, patterns)


def normalize_extra_patterns(extra_patterns: Iterable[str]) -> tuple[str, ...]:
    return tuple(pattern for pattern in extra_patterns if pattern)


class IgnoreManager:
    """Provides gitignore-aware file filtering for discovery tools."""

    def __init__(
        self,
        root: Path,
        patterns: Iterable[str],
        exclude_dirs: frozenset[str],
    ) -> None:
        """Precondition: root exists and is a directory."""

        self._root = root
        patterns_tuple = tuple(patterns)
        self._patterns = patterns_tuple
        self._exclude_dirs = exclude_dirs
        self._spec = compile_spec(patterns_tuple)

    def should_ignore(self, path: Path) -> bool:
        relative_path = self._normalize_path(path)
        if self._is_fast_excluded(relative_path):
            return True
        return self._spec.match_file(relative_path.as_posix())

    def should_ignore_dir(self, path: Path) -> bool:
        relative_path = self._normalize_path(path)
        if self._is_fast_excluded(relative_path):
            return True

        rel_posix = relative_path.as_posix()
        if self._spec.match_file(rel_posix):
            return True

        dir_path = f"{rel_posix}{PATH_SEPARATOR}"
        return self._spec.match_file(dir_path)

    def filter_paths(self, paths: Iterable[Path]) -> Iterator[Path]:
        for path in paths:
            if self.should_ignore(path):
                continue
            yield path

    def with_additional_patterns(self, extra_patterns: Iterable[str]) -> IgnoreManager:
        normalized_patterns = normalize_extra_patterns(extra_patterns)
        if not normalized_patterns:
            return self

        combined_patterns = self._patterns + normalized_patterns
        return IgnoreManager(
            root=self._root,
            patterns=combined_patterns,
            exclude_dirs=self._exclude_dirs,
        )

    def _normalize_path(self, path: Path) -> Path:
        candidate_path = path if path.is_absolute() else self._root / path
        try:
            return candidate_path.relative_to(self._root)
        except ValueError as exc:
            message = PATH_OUTSIDE_ROOT_ERROR.format(path=candidate_path, root=self._root)
            raise ValueError(message) from exc

    def _is_fast_excluded(self, relative_path: Path) -> bool:
        return any(part in self._exclude_dirs for part in relative_path.parts)


def create_ignore_manager(
    *,
    root: Path,
    gitignore_lines: tuple[str, ...],
) -> IgnoreManager:
    patterns = build_patterns(gitignore_lines)
    return IgnoreManager(root=root, patterns=patterns, exclude_dirs=DEFAULT_EXCLUDE_DIRS)
