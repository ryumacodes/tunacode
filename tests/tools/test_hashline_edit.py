"""Tests for the hashline_edit tool."""

import os
import tempfile

import pytest

from tunacode.exceptions import ToolRetryError

import tunacode.tools.line_cache as line_cache
from tunacode.tools.hashline import HashedLine, content_hash
from tunacode.tools.hashline_edit import (
    _apply_insert_after,
    _apply_replace,
    _apply_replace_range,
    _validate_ref,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Ensure each test starts with a clean cache."""
    line_cache.clear()


def _cache_file(filepath: str, contents: list[str]) -> None:
    """Populate the line cache for a file."""
    lines = [
        HashedLine(line_number=i + 1, hash=content_hash(c), content=c)
        for i, c in enumerate(contents)
    ]
    line_cache.store(filepath, lines)


def _make_ref(content: str, line_number: int) -> str:
    """Build a line:hash reference string."""
    h = content_hash(content)
    return f"{line_number}:{h}"


class TestValidateRef:
    def test_valid_ref(self) -> None:
        _cache_file("/tmp/f.py", ["hello", "world"])
        ref = _make_ref("hello", 1)
        assert _validate_ref("/tmp/f.py", ref) == 1

    def test_uncached_file(self) -> None:
        ref = _make_ref("hello", 1)
        with pytest.raises(ToolRetryError, match="no cached state"):
            _validate_ref("/tmp/f.py", ref)

    def test_missing_line(self) -> None:
        _cache_file("/tmp/f.py", ["hello"])
        ref = _make_ref("hello", 99)
        with pytest.raises(ToolRetryError, match="not in the cached state"):
            _validate_ref("/tmp/f.py", ref)

    def test_stale_hash(self) -> None:
        _cache_file("/tmp/f.py", ["hello"])
        # Use wrong hash
        with pytest.raises(ToolRetryError, match="hash mismatch"):
            _validate_ref("/tmp/f.py", "1:zz")


class TestApplyReplace:
    def test_replace_line(self) -> None:
        contents = ["def foo():", "    return 1", ""]
        _cache_file("/tmp/f.py", contents)
        ref = _make_ref("    return 1", 2)

        new_lines, desc = _apply_replace("/tmp/f.py", contents, ref, "    return 2")
        assert new_lines == ["def foo():", "    return 2", ""]
        assert "replaced line 2" in desc

    def test_replace_missing_param(self) -> None:
        with pytest.raises(ToolRetryError, match="'line' parameter is required"):
            _apply_replace("/tmp/f.py", ["x"], None, "y")

    def test_replace_out_of_range(self) -> None:
        contents = ["only line"]
        _cache_file("/tmp/f.py", contents)
        # Manually add a cache entry for a line beyond file length
        h = content_hash("ghost")
        line_cache.get("/tmp/f.py")[99] = HashedLine(99, h, "ghost")  # type: ignore[index]

        with pytest.raises(ToolRetryError, match="out of range"):
            _apply_replace("/tmp/f.py", contents, f"99:{h}", "new")


class TestApplyReplaceRange:
    def test_replace_range(self) -> None:
        contents = ["a", "b", "c", "d"]
        _cache_file("/tmp/f.py", contents)
        start = _make_ref("b", 2)
        end = _make_ref("c", 3)

        new_lines, desc = _apply_replace_range(
            "/tmp/f.py", contents, start, end, "X\nY\nZ",
        )
        assert new_lines == ["a", "X", "Y", "Z", "d"]
        assert "replaced lines 2-3" in desc

    def test_replace_range_to_empty(self) -> None:
        contents = ["a", "b", "c"]
        _cache_file("/tmp/f.py", contents)
        start = _make_ref("b", 2)
        end = _make_ref("b", 2)

        new_lines, _ = _apply_replace_range(
            "/tmp/f.py", contents, start, end, "",
        )
        assert new_lines == ["a", "c"]

    def test_replace_range_missing_start(self) -> None:
        with pytest.raises(ToolRetryError, match="'start' parameter is required"):
            _apply_replace_range("/tmp/f.py", ["x"], None, "1:ab", "y")

    def test_replace_range_missing_end(self) -> None:
        _cache_file("/tmp/f.py", ["x"])
        with pytest.raises(ToolRetryError, match="'end' parameter is required"):
            _apply_replace_range("/tmp/f.py", ["x"], _make_ref("x", 1), None, "y")

    def test_replace_range_start_after_end(self) -> None:
        contents = ["a", "b"]
        _cache_file("/tmp/f.py", contents)
        start = _make_ref("b", 2)
        end = _make_ref("a", 1)

        with pytest.raises(ToolRetryError, match="must not be greater"):
            _apply_replace_range("/tmp/f.py", contents, start, end, "x")


class TestApplyInsertAfter:
    def test_insert_after(self) -> None:
        contents = ["a", "b", "c"]
        _cache_file("/tmp/f.py", contents)
        ref = _make_ref("b", 2)

        new_lines, desc = _apply_insert_after(
            "/tmp/f.py", contents, ref, "X\nY",
        )
        assert new_lines == ["a", "b", "X", "Y", "c"]
        assert "inserted 2 line(s)" in desc

    def test_insert_after_last_line(self) -> None:
        contents = ["a", "b"]
        _cache_file("/tmp/f.py", contents)
        ref = _make_ref("b", 2)

        new_lines, _ = _apply_insert_after(
            "/tmp/f.py", contents, ref, "c",
        )
        assert new_lines == ["a", "b", "c"]

    def test_insert_after_missing_param(self) -> None:
        with pytest.raises(ToolRetryError, match="'after' parameter is required"):
            _apply_insert_after("/tmp/f.py", ["x"], None, "y")


class TestHashlineEditIntegration:
    """Integration tests that exercise the full async tool function."""

    @pytest.fixture
    def temp_file(self) -> str:
        """Create a temp file with known content."""
        fd, path = tempfile.mkstemp(suffix=".py")
        with os.fdopen(fd, "w") as f:
            f.write("line one\nline two\nline three\n")
        yield path  # type: ignore[misc]
        os.unlink(path)

    @pytest.mark.asyncio
    async def test_full_replace(self, temp_file: str) -> None:
        from tunacode.tools.hashline_edit import hashline_edit

        # First populate the cache by simulating what read_file does
        with open(temp_file) as f:
            lines_content = [raw.rstrip("\n") for raw in f.readlines()]
        _cache_file(temp_file, lines_content)

        ref = _make_ref("line two", 2)
        result = await hashline_edit(
            filepath=temp_file,
            operation="replace",
            line=ref,
            new="LINE TWO",
        )

        assert "updated" in result

        with open(temp_file) as f:
            content = f.read()
        assert "LINE TWO" in content
        assert "line two" not in content

    @pytest.mark.asyncio
    async def test_full_insert_after(self, temp_file: str) -> None:
        from tunacode.tools.hashline_edit import hashline_edit

        with open(temp_file) as f:
            lines_content = [raw.rstrip("\n") for raw in f.readlines()]
        _cache_file(temp_file, lines_content)

        ref = _make_ref("line one", 1)
        result = await hashline_edit(
            filepath=temp_file,
            operation="insert_after",
            after=ref,
            new="inserted line",
        )

        assert "inserted" in result

        with open(temp_file) as f:
            content = f.read()
        assert "inserted line" in content

    @pytest.mark.asyncio
    async def test_stale_ref_rejected(self, temp_file: str) -> None:
        from tunacode.tools.hashline_edit import hashline_edit

        # Cache the file
        with open(temp_file) as f:
            lines_content = [raw.rstrip("\n") for raw in f.readlines()]
        _cache_file(temp_file, lines_content)

        # Modify the file on disk without updating cache
        with open(temp_file, "w") as f:
            f.write("totally different content\n")

        # Try to edit with stale hash — should be rejected
        ref = _make_ref("line two", 2)
        # The hash check is against the cache, not the disk.
        # The cache still has the old content, and the ref matches,
        # so this will succeed against the cache. The stale detection
        # happens when the model provides a ref whose hash no longer
        # matches what's in the cache (e.g., after another edit).

        # Simulate: corrupt the cache to mismatch
        line_cache.update_lines(temp_file, {2: "changed line"})

        with pytest.raises(ToolRetryError, match="hash mismatch"):
            await hashline_edit(
                filepath=temp_file,
                operation="replace",
                line=ref,
                new="wont work",
            )
