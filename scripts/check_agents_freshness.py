#!/usr/bin/env python3
"""Validate AGENTS.md freshness against recent repository changes."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DATE_FORMAT = "%Y-%m-%d"
LAST_UPDATED_PATTERN = re.compile(r"^Last Updated: (\d{4}-\d{2}-\d{2})$")

AGENTS_PATH = Path("AGENTS.md")
TRACKED_PATHS = (Path("src"), Path("docs"))


@dataclass(frozen=True)
class FreshnessStatus:
    last_updated: datetime
    latest_commit: datetime


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_last_updated(content: str) -> datetime:
    for line in content.splitlines():
        match = LAST_UPDATED_PATTERN.match(line.strip())
        if match:
            return datetime.strptime(match.group(1), DATE_FORMAT)
    raise ValueError("AGENTS.md missing 'Last Updated: YYYY-MM-DD' line")


def _load_latest_commit_date(paths: tuple[Path, ...]) -> datetime:
    command = [
        "git",
        "log",
        "-1",
        "--format=%cs",
        "--",
        *[path.as_posix() for path in paths],
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        error = result.stderr.strip() or "unknown git error"
        raise RuntimeError(f"git log failed: {error}")

    output = result.stdout.strip()
    if not output:
        raise RuntimeError("git log returned no commit date")

    return datetime.strptime(output, DATE_FORMAT)


def _get_freshness_status() -> FreshnessStatus:
    if not AGENTS_PATH.exists():
        raise FileNotFoundError(f"Missing {AGENTS_PATH}")

    content = _read_text(AGENTS_PATH)
    last_updated = _parse_last_updated(content)
    latest_commit = _load_latest_commit_date(TRACKED_PATHS)
    return FreshnessStatus(last_updated=last_updated, latest_commit=latest_commit)


def main() -> int:
    status = _get_freshness_status()

    if status.last_updated < status.latest_commit:
        last_updated = status.last_updated.strftime(DATE_FORMAT)
        latest_commit = status.latest_commit.strftime(DATE_FORMAT)
        message = (
            "AGENTS.md is stale. "
            f"Last Updated: {last_updated}, "
            f"latest repo change in src/docs: {latest_commit}."
        )
        print(message)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
