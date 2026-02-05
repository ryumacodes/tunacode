from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

import pathspec
from textual.fuzzy import FuzzySearch

FUZZY_CASE_SENSITIVE = False
FUZZY_MATCH_SCORE_THRESHOLD = 0.0


class FileFilter:
    """Gitignore-aware file filtering."""

    def __init__(
        self,
        ignore_patterns: Sequence[str],
        result_limit: int,
        max_depth: int,
        root: Path | None = None,
    ) -> None:
        self.root = root or Path(".")
        self._ignore_patterns = tuple(ignore_patterns)
        self._result_limit = result_limit
        self._max_depth = max_depth
        self._spec = self._build_spec()

    def _build_spec(self) -> pathspec.PathSpec:
        patterns = list(self._ignore_patterns)
        gitignore = self.root / ".gitignore"
        if gitignore.exists():
            patterns.extend(gitignore.read_text().splitlines())
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    def is_ignored(self, path: Path) -> bool:
        try:
            rel = path.relative_to(self.root)
            return self._spec.match_file(str(rel))
        except ValueError:
            return False

    def _parse_prefix(self, prefix: str) -> tuple[Path, str]:
        """Parse prefix into search path and name filter."""
        if not prefix:
            return self.root, ""

        candidate = self.root / prefix

        if candidate.exists() and candidate.is_dir():
            return candidate, ""

        search_path = candidate.parent
        name_prefix = Path(prefix).name

        if not search_path.exists():
            return self.root, ""

        return search_path, name_prefix

    def _is_fuzzy_match(
        self,
        fuzzy_search: FuzzySearch,
        query: str,
        candidate: str,
    ) -> bool:
        score, _ = fuzzy_search.match(query, candidate)
        return score > FUZZY_MATCH_SCORE_THRESHOLD

    def _matches_prefix(self, path: Path, name_prefix: str, search_path: Path) -> bool:
        """Check if path matches name prefix filter."""
        if not name_prefix:
            return True

        fuzzy_search = FuzzySearch(case_sensitive=FUZZY_CASE_SENSITIVE)

        if path.parent == search_path:
            candidate = path.name
            return self._is_fuzzy_match(fuzzy_search, name_prefix, candidate)

        rel_path = path.relative_to(search_path)
        return any(self._is_fuzzy_match(fuzzy_search, name_prefix, part) for part in rel_path.parts)

    def _collect_dirs(
        self,
        dirs: list[str],
        root_path: Path,
        name_prefix: str,
        search_path: Path,
        current_depth: int,
        results: list[tuple[int, str]],
        result_limit: int,
    ) -> bool:
        """Collect matching directories into results. Returns True when limit reached."""
        for d in dirs:
            dir_path = root_path / d
            if not self._matches_prefix(dir_path, name_prefix, search_path):
                continue
            rel = dir_path.relative_to(self.root)
            results.append((current_depth, f"{rel}/"))
            if len(results) >= result_limit:
                return True
        return False

    def _collect_files(
        self,
        files: list[str],
        root_path: Path,
        name_prefix: str,
        search_path: Path,
        current_depth: int,
        results: list[tuple[int, str]],
        result_limit: int,
    ) -> bool:
        """Collect matching files into results. Returns True when limit reached."""
        for f in sorted(files):
            file_path = root_path / f
            if self.is_ignored(file_path):
                continue
            if not self._matches_prefix(file_path, name_prefix, search_path):
                continue
            rel = file_path.relative_to(self.root)
            results.append((current_depth, str(rel)))
            if len(results) >= result_limit:
                return True
        return False

    def complete(
        self,
        prefix: str = "",
        limit: int | None = None,
        max_depth: int | None = None,
    ) -> list[str]:
        """Return filtered file paths matching prefix."""
        search_path, name_prefix = self._parse_prefix(prefix)

        if not search_path.exists():
            return []

        effective_limit = self._result_limit if limit is None else limit
        effective_max_depth = self._max_depth if max_depth is None else max_depth

        results_with_depth: list[tuple[int, str]] = []

        for root_dir, dirs, files in os.walk(str(search_path), topdown=True):
            root_path = Path(root_dir)
            rel_root = root_path.relative_to(search_path)
            current_depth = len(rel_root.parts)

            if current_depth >= effective_max_depth:
                dirs[:] = []

            dirs[:] = sorted(d for d in dirs if not self.is_ignored(root_path / d))

            dirs_full = self._collect_dirs(
                dirs,
                root_path,
                name_prefix,
                search_path,
                current_depth,
                results_with_depth,
                effective_limit,
            )
            if dirs_full:
                break

            files_full = self._collect_files(
                files,
                root_path,
                name_prefix,
                search_path,
                current_depth,
                results_with_depth,
                effective_limit,
            )
            if files_full:
                break

        results_with_depth.sort(key=lambda x: (x[0], x[1]))
        return [path for _, path in results_with_depth[:effective_limit]]
