"""
Module: tunacode.utils.system.gitignore

Provides repository file listing with shared ignore-rule support.
"""

import os
from pathlib import Path

import pathspec

from tunacode.configuration.ignore_patterns import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_IGNORE_PATTERNS,
    GITIGNORE_FILE_NAME,
    compile_ignore_spec,
    merge_ignore_patterns,
    read_ignore_file_lines,
)


def _is_fast_excluded(relative_path: Path) -> bool:
    return any(part in DEFAULT_EXCLUDE_DIRS for part in relative_path.parts)


def _matches_ignored_path(relative_path: Path, spec: pathspec.PathSpec, is_dir: bool) -> bool:
    if _is_fast_excluded(relative_path):
        return True

    rel_posix = relative_path.as_posix()
    if spec.match_file(rel_posix):
        return True

    return is_dir and spec.match_file(f"{rel_posix}/")


def list_cwd(max_depth: int = 3) -> list[str]:
    """
    Lists files in the current working directory up to a specified depth,
    respecting .gitignore rules or a default ignore list.

    Args:
        max_depth (int): Maximum directory depth to traverse.
                         0: only files in the current directory.
                         1: includes files in immediate subdirectories.
                         ... Default is 3.

    Returns:
        list: A sorted list of relative file paths.
    """
    file_list = []
    start_path = Path(".")
    gitignore = start_path / GITIGNORE_FILE_NAME
    patterns = merge_ignore_patterns(DEFAULT_IGNORE_PATTERNS, read_ignore_file_lines(gitignore))
    spec = compile_ignore_spec(patterns)
    max_depth = max(0, max_depth)

    for root, dirs, files in os.walk(start_path, topdown=True):
        root_path = Path(root)
        rel_root = root_path.relative_to(start_path)
        current_depth = len(rel_root.parts)

        if current_depth >= max_depth:
            dirs[:] = []

        original_dirs = list(dirs)
        dirs[:] = []
        for d in original_dirs:
            dir_rel_path = rel_root / d
            if not _matches_ignored_path(dir_rel_path, spec, is_dir=True):
                dirs.append(d)

        if current_depth <= max_depth:
            for f in files:
                file_rel_path = rel_root / f
                if not _matches_ignored_path(file_rel_path, spec, is_dir=False):
                    file_list.append(file_rel_path.as_posix())

    return sorted(file_list)
