"""Tests for the read_file tool."""

from pathlib import Path

import pytest
from kosong.tooling import ToolError, ToolOk

from kimi_cli.agent import BuiltinSystemPromptArgs
from kimi_cli.tools.file.read import ReadFile


@pytest.fixture
def read_file_tool(builtin_args: BuiltinSystemPromptArgs) -> ReadFile:
    """Create a ReadFile tool instance."""
    return ReadFile(builtin_args)


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


@pytest.mark.asyncio
async def test_read_entire_file(read_file_tool: ReadFile, sample_file: Path):
    """Test reading an entire file."""
    result = await read_file_tool(str(sample_file))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "5 lines read from" in result.message
    assert "     1\tLine 1: Hello World" in result.output
    assert "     5\tLine 5: End of file" in result.output


@pytest.mark.asyncio
async def test_read_with_line_offset(read_file_tool: ReadFile, sample_file: Path):
    """Test reading from a specific line offset."""
    result = await read_file_tool(str(sample_file), line_offset=3)

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "3 lines read from" in result.message  # Lines 3, 4, 5
    assert "     3\tLine 3: With multiple lines" in result.output
    assert "Line 1" not in result.output  # First two lines should be skipped
    assert "     5\tLine 5: End of file" in result.output


@pytest.mark.asyncio
async def test_read_with_n_lines(read_file_tool: ReadFile, sample_file: Path):
    """Test reading a specific number of lines."""
    result = await read_file_tool(str(sample_file), n_lines=2)

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "2 lines read from" in result.message
    assert "     1\tLine 1: Hello World" in result.output
    assert "     2\tLine 2: This is a test file" in result.output
    assert "Line 3" not in result.output  # Should not include line 3


@pytest.mark.asyncio
async def test_read_with_line_offset_and_n_lines(read_file_tool: ReadFile, sample_file: Path):
    """Test reading with both line offset and n_lines."""
    result = await read_file_tool(str(sample_file), line_offset=2, n_lines=2)

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "2 lines read from" in result.message
    assert "     2\tLine 2: This is a test file" in result.output
    assert "     3\tLine 3: With multiple lines" in result.output
    assert "Line 1" not in result.output
    assert "Line 4" not in result.output


@pytest.mark.asyncio
async def test_read_nonexistent_file(read_file_tool: ReadFile, temp_work_dir: Path):
    """Test reading a non-existent file."""
    nonexistent_file = temp_work_dir / "nonexistent.txt"
    result = await read_file_tool(str(nonexistent_file))

    assert isinstance(result, ToolError)
    assert "does not exist" in result.message


@pytest.mark.asyncio
async def test_read_directory_instead_of_file(read_file_tool: ReadFile, temp_work_dir: Path):
    """Test attempting to read a directory."""
    result = await read_file_tool(str(temp_work_dir))

    assert isinstance(result, ToolError)
    assert "is not a file" in result.message


@pytest.mark.asyncio
async def test_read_with_relative_path(read_file_tool: ReadFile):
    """Test reading with a relative path (should fail)."""
    result = await read_file_tool("relative/path/file.txt")

    assert isinstance(result, ToolError)
    assert "not an absolute path" in result.message


@pytest.mark.asyncio
async def test_read_empty_file(read_file_tool: ReadFile, temp_work_dir: Path):
    """Test reading an empty file."""
    empty_file = temp_work_dir / "empty.txt"
    empty_file.write_text("")

    result = await read_file_tool(str(empty_file))

    assert isinstance(result, ToolOk)
    assert result.output == ""
    assert "No lines read from" in result.message


@pytest.mark.asyncio
async def test_read_line_offset_beyond_file_length(read_file_tool: ReadFile, sample_file: Path):
    """Test reading with line offset beyond file length."""
    result = await read_file_tool(str(sample_file), line_offset=10)

    assert isinstance(result, ToolOk)
    assert result.output == ""
    assert "No lines read from" in result.message


@pytest.mark.asyncio
async def test_read_unicode_file(read_file_tool: ReadFile, temp_work_dir: Path):
    """Test reading a file with unicode characters."""
    unicode_file = temp_work_dir / "unicode.txt"
    content = "Hello 世界 🌍\nUnicode test: café, naïve, résumé"
    unicode_file.write_text(content, encoding="utf-8")

    result = await read_file_tool(str(unicode_file))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "世界" in result.output
    assert "🌍" in result.output
    assert "café" in result.output


@pytest.mark.asyncio
async def test_read_edge_cases(read_file_tool: ReadFile, sample_file: Path):
    """Test edge cases for line offset reading."""
    # Test reading from line 1 (should be same as default)
    result = await read_file_tool(str(sample_file), line_offset=1)
    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "5 lines read from" in result.message

    # Test reading from line 5 (last line)
    result = await read_file_tool(str(sample_file), line_offset=5)
    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "1 lines read from" in result.message
    assert "     5\tLine 5: End of file" in result.output

    # Test reading with offset and n_lines combined
    result = await read_file_tool(str(sample_file), line_offset=2, n_lines=1)
    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "1 lines read from" in result.message
    assert "     2\tLine 2: This is a test file" in result.output
    assert "Line 1" not in result.output
    assert "Line 3" not in result.output


@pytest.mark.asyncio
async def test_long_line_truncation(read_file_tool: ReadFile, temp_work_dir: Path):
    """Test that long lines are truncated properly."""
    long_line_file = temp_work_dir / "long_line.txt"
    # Create a line longer than 2000 characters
    long_content = "A" * 2500 + " This should be truncated"
    long_line_file.write_text(long_content)

    result = await read_file_tool(str(long_line_file))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "1 lines read from" in result.message
    # Check that the line is truncated and ends with "..."
    assert result.output.endswith("...")
    # The total length should be exactly 2000 characters (accounting for line number prefix)
    lines = result.output.split("\n")
    content_line = [
        line for line in lines if line.strip() and not line.startswith("<system-message>")
    ][0]
    # Extract just the content part after the tab
    actual_content = content_line.split("\t", 1)[1] if "\t" in content_line else content_line
    assert len(actual_content) == 2000
