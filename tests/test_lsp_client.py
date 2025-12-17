"""Integration tests for the LSP client.

Tests the LSP client against a real language server (pyright).
Skips if pyright is not installed.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

# Skip entire module if pyright is not installed
pytestmark = pytest.mark.skipif(
    shutil.which("pyright-langserver") is None,
    reason="pyright-langserver not installed",
)


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_file.py"
        yield filepath


class TestLSPClient:
    """Integration tests for LSP client with pyright."""

    @pytest.mark.asyncio
    async def test_receives_diagnostics_for_file_with_errors(self, temp_python_file):
        """LSP client receives diagnostics for a file with type errors."""
        from tunacode.lsp import get_diagnostics

        # Create a file with an obvious type error
        temp_python_file.write_text(
            """
def add(a: int, b: int) -> int:
    return a + b

result: str = add(1, 2)  # Type error: int assigned to str
""",
            encoding="utf-8",
        )

        diagnostics = await get_diagnostics(temp_python_file, timeout=10.0)

        # Should receive at least one diagnostic about type mismatch
        assert len(diagnostics) > 0
        # Check that we have line info and a message
        diag = diagnostics[0]
        assert diag.line > 0
        assert len(diag.message) > 0

    @pytest.mark.asyncio
    async def test_no_diagnostics_for_valid_file(self, temp_python_file):
        """LSP client returns empty list for valid file."""
        from tunacode.lsp import get_diagnostics

        # Create a valid Python file
        temp_python_file.write_text(
            """
def add(a: int, b: int) -> int:
    return a + b

result: int = add(1, 2)
""",
            encoding="utf-8",
        )

        diagnostics = await get_diagnostics(temp_python_file, timeout=10.0)

        # Should have no diagnostics for valid code
        assert len(diagnostics) == 0

    @pytest.mark.asyncio
    async def test_format_diagnostics_output(self, temp_python_file):
        """Diagnostics are formatted as XML block."""
        from tunacode.lsp import format_diagnostics, get_diagnostics

        # Create a file with a syntax error
        temp_python_file.write_text(
            """
x: int = "hello"  # Type error
""",
            encoding="utf-8",
        )

        diagnostics = await get_diagnostics(temp_python_file, timeout=10.0)
        output = format_diagnostics(diagnostics)

        if diagnostics:
            assert "<file_diagnostics>" in output
            assert "</file_diagnostics>" in output
            assert "line" in output.lower()


class TestLSPServerAvailability:
    """Tests for server availability detection."""

    @pytest.mark.asyncio
    async def test_graceful_fallback_for_unsupported_extension(self, temp_python_file):
        """Returns empty list for unsupported file extensions."""
        from tunacode.lsp import get_diagnostics

        # Create a file with unsupported extension
        unsupported_file = temp_python_file.with_suffix(".xyz")
        unsupported_file.write_text("some content", encoding="utf-8")

        diagnostics = await get_diagnostics(unsupported_file, timeout=2.0)

        assert diagnostics == []

    @pytest.mark.asyncio
    async def test_graceful_fallback_for_nonexistent_file(self):
        """Returns empty list for nonexistent file."""
        from tunacode.lsp import get_diagnostics

        diagnostics = await get_diagnostics(Path("/nonexistent/path/file.py"), timeout=2.0)

        assert diagnostics == []
