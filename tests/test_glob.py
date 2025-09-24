"""Tests for the glob tool."""

from pathlib import Path

import pytest
from kosong.tooling import ToolError, ToolOk

from kimi_cli.agent import BuiltinSystemPromptArgs
from kimi_cli.tools.file import Glob


@pytest.fixture
def glob_tool(builtin_args: BuiltinSystemPromptArgs) -> Glob:
    """Create a Glob tool instance."""
    return Glob(builtin_args)


@pytest.fixture
def test_files(temp_work_dir: Path):
    """Create test files for glob testing."""
    # Create a directory structure
    (temp_work_dir / "src" / "main").mkdir(parents=True)
    (temp_work_dir / "src" / "test").mkdir(parents=True)
    (temp_work_dir / "docs").mkdir()

    # Create test files
    (temp_work_dir / "README.md").write_text("# README")
    (temp_work_dir / "setup.py").write_text("setup")
    (temp_work_dir / "src" / "main.py").write_text("main")
    (temp_work_dir / "src" / "utils.py").write_text("utils")
    (temp_work_dir / "src" / "main" / "app.py").write_text("app")
    (temp_work_dir / "src" / "main" / "config.py").write_text("config")
    (temp_work_dir / "src" / "test" / "test_app.py").write_text("test app")
    (temp_work_dir / "src" / "test" / "test_config.py").write_text("test config")
    (temp_work_dir / "docs" / "guide.md").write_text("guide")
    (temp_work_dir / "docs" / "api.md").write_text("api")

    return temp_work_dir


@pytest.mark.asyncio
async def test_glob_simple_pattern(glob_tool: Glob, test_files: Path):
    """Test simple glob pattern matching."""
    result = await glob_tool("*.py", str(test_files))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "setup.py" in result.output
    assert "Found 1 matches" in result.message


@pytest.mark.asyncio
async def test_glob_multiple_matches(glob_tool: Glob, test_files: Path):
    """Test glob pattern with multiple matches."""
    result = await glob_tool("*.md", str(test_files))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "README.md" in result.output
    assert "Found 1 matches" in result.message


@pytest.mark.asyncio
async def test_glob_recursive_pattern_prohibited(glob_tool: Glob, test_files: Path):
    """Test that recursive glob pattern starting with **/ is prohibited."""
    result = await glob_tool("**/*.py", str(test_files))

    assert isinstance(result, ToolError)
    assert "starts with '**' which is not allowed" in result.message
    assert "Unsafe pattern" in result.brief


@pytest.mark.asyncio
async def test_glob_safe_recursive_pattern(glob_tool: Glob, test_files: Path):
    """Test safe recursive glob pattern that doesn't start with **/."""
    result = await glob_tool("src/**/*.py", str(test_files))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "src/main.py" in result.output
    assert "src/utils.py" in result.output
    assert "src/main/app.py" in result.output
    assert "src/main/config.py" in result.output
    assert "src/test/test_app.py" in result.output
    assert "src/test/test_config.py" in result.output
    assert "Found 6 matches" in result.message


@pytest.mark.asyncio
async def test_glob_specific_directory(glob_tool: Glob, test_files: Path):
    """Test glob pattern in specific directory."""
    src_dir = str(test_files / "src")
    result = await glob_tool("*.py", src_dir)

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "main.py" in result.output
    assert "utils.py" in result.output
    assert "Found 2 matches" in result.message


@pytest.mark.asyncio
async def test_glob_recursive_in_subdirectory(glob_tool: Glob, test_files: Path):
    """Test recursive glob in subdirectory."""
    src_dir = str(test_files / "src")
    result = await glob_tool("main/**/*.py", src_dir)

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "main/app.py" in result.output
    assert "main/config.py" in result.output
    assert "Found 2 matches" in result.message


@pytest.mark.asyncio
async def test_glob_test_files(glob_tool: Glob, test_files: Path):
    """Test glob pattern for test files."""
    result = await glob_tool("src/**/*test*.py", str(test_files))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "src/test/test_app.py" in result.output
    assert "src/test/test_config.py" in result.output
    assert "Found 2 matches" in result.message


@pytest.mark.asyncio
async def test_glob_no_matches(glob_tool: Glob, test_files: Path):
    """Test glob pattern with no matches."""
    result = await glob_tool("*.xyz", str(test_files))

    assert isinstance(result, ToolOk)
    assert result.output == ""
    assert "No files or directories found" in result.message


@pytest.mark.asyncio
async def test_glob_exclude_directories(glob_tool: Glob, temp_work_dir: Path):
    """Test glob with include_dirs=False."""
    # Create both files and directories
    (temp_work_dir / "test_file.txt").write_text("content")
    (temp_work_dir / "test_dir").mkdir()

    result = await glob_tool("test_*", str(temp_work_dir), include_dirs=False)

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "test_file.txt" in result.output
    assert "test_dir" not in result.output
    assert "Found 1 matches" in result.message


@pytest.mark.asyncio
async def test_glob_with_relative_path(glob_tool: Glob):
    """Test glob with relative path (should fail)."""
    result = await glob_tool("*.py", "relative/path")

    assert isinstance(result, ToolError)
    assert "not an absolute path" in result.message


@pytest.mark.asyncio
async def test_glob_outside_work_directory(glob_tool: Glob):
    """Test glob outside working directory (should fail)."""
    result = await glob_tool("*.py", "/tmp/outside")

    assert isinstance(result, ToolError)
    assert "outside the working directory" in result.message


@pytest.mark.asyncio
async def test_glob_nonexistent_directory(glob_tool: Glob, temp_work_dir: Path):
    """Test glob in nonexistent directory."""
    nonexistent_dir = str(temp_work_dir / "nonexistent")
    result = await glob_tool("*.py", nonexistent_dir)

    assert isinstance(result, ToolError)
    assert "does not exist" in result.message


@pytest.mark.asyncio
async def test_glob_not_a_directory(glob_tool: Glob, temp_work_dir: Path):
    """Test glob on a file instead of directory."""
    test_file = temp_work_dir / "test.txt"
    test_file.write_text("content")

    result = await glob_tool("*.py", str(test_file))

    assert isinstance(result, ToolError)
    assert "is not a directory" in result.message


@pytest.mark.asyncio
async def test_glob_single_character_wildcard(glob_tool: Glob, test_files: Path):
    """Test single character wildcard."""
    result = await glob_tool("?.md", str(test_files))

    assert isinstance(result, ToolOk)
    assert result.output == ""
    # Should match single character .md files


@pytest.mark.asyncio
async def test_glob_character_class(glob_tool: Glob, temp_work_dir: Path):
    """Test character class pattern."""
    (temp_work_dir / "file1.py").write_text("content1")
    (temp_work_dir / "file2.py").write_text("content2")
    (temp_work_dir / "file3.txt").write_text("content3")

    result = await glob_tool("file[1-2].py", str(temp_work_dir))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "file1.py" in result.output
    assert "file2.py" in result.output
    assert "file3.txt" not in result.output


@pytest.mark.asyncio
async def test_glob_complex_pattern(glob_tool: Glob, test_files: Path):
    """Test complex glob pattern combinations."""
    result = await glob_tool("docs/**/main/*.py", str(test_files))

    assert isinstance(result, ToolOk)
    assert result.output == ""
    # Should not match anything since there are no Python files in docs/main


@pytest.mark.asyncio
async def test_glob_wildcard_with_double_star_patterns(glob_tool: Glob, test_files: Path):
    """Test various patterns with ** that are allowed."""
    # Test pattern with ** in the middle
    result = await glob_tool("**/main/*.py", str(test_files))

    assert isinstance(result, ToolError)
    assert "starts with '**' which is not allowed" in result.message

    # Test pattern with ** not at the beginning
    result = await glob_tool("src/**/test_*.py", str(test_files))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "src/test/test_app.py" in result.output
    assert "src/test/test_config.py" in result.output


@pytest.mark.asyncio
async def test_glob_pattern_edge_cases(glob_tool: Glob, test_files: Path):
    """Test edge cases for pattern validation."""
    # Test pattern that has ** but not at the start
    result = await glob_tool("src/**", str(test_files))
    assert isinstance(result, ToolOk)

    # Test pattern that starts with * but not **
    result = await glob_tool("*.py", str(test_files))
    assert isinstance(result, ToolOk)

    # Test pattern that starts with **/
    result = await glob_tool("**/*.txt", str(test_files))
    assert isinstance(result, ToolError)
    assert "starts with '**' which is not allowed" in result.message
