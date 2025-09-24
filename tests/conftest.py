"""Test configuration and fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from kimi_cli.agent import BuiltinSystemPromptArgs


@pytest.fixture
def temp_work_dir() -> Generator[Path]:
    """Create a temporary working directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def builtin_args(temp_work_dir: Path) -> BuiltinSystemPromptArgs:
    """Create builtin arguments with temporary work directory."""
    return BuiltinSystemPromptArgs(
        ENSOUL_WORK_DIR=temp_work_dir,
        ENSOUL_WORK_DIR_LS="Test ls content",
        ENSOUL_AGENTS_MD="Test agents content",
    )
