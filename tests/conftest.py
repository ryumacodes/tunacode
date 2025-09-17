"""Test configuration and fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from kimi_cli.agent import BuiltinSystemPromptArgs
from kimi_cli.tools.file.read import ReadFile
from kimi_cli.tools.file.write import WriteFile
from kimi_cli.tools.shell import Shell


@pytest.fixture
def temp_work_dir() -> Generator[Path]:
    """Create a temporary working directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def builtin_args(temp_work_dir: Path) -> BuiltinSystemPromptArgs:
    """Create builtin arguments with temporary work directory."""
    return BuiltinSystemPromptArgs(ENSOUL_WORK_DIR=temp_work_dir, ENSOUL_AGENTS_MD="")


@pytest.fixture
def read_file_tool(builtin_args: BuiltinSystemPromptArgs) -> ReadFile:
    """Create a ReadFile tool instance."""
    return ReadFile(builtin_args)


@pytest.fixture
def write_file_tool(builtin_args: BuiltinSystemPromptArgs) -> WriteFile:
    """Create a WriteFile tool instance."""
    return WriteFile(builtin_args)


@pytest.fixture
def shell_tool() -> Shell:
    """Create a Shell tool instance."""
    return Shell()


@pytest.fixture
def sample_file(temp_work_dir: Path) -> Path:
    """Create a sample file with test content."""
    file_path = temp_work_dir / "sample.txt"
    content = """Line 1: Hello World
Line 2: This is a test file
Line 3: With multiple lines
Line 4: For testing purposes
Line 5: End of file"""
    file_path.write_text(content)
    return file_path
