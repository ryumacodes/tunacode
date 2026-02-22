"""Tests for the line cache module."""

import pytest

import tunacode.tools.line_cache as line_cache
from tunacode.tools.hashline import HashedLine, content_hash


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Ensure each test starts with a clean cache."""
    line_cache.clear()


def _make_lines(contents: list[str], offset: int = 0) -> list[HashedLine]:
    return [
        HashedLine(
            line_number=offset + i + 1,
            hash=content_hash(c),
            content=c,
        )
        for i, c in enumerate(contents)
    ]


class TestStoreAndGet:
    def test_store_and_retrieve(self) -> None:
        lines = _make_lines(["a", "b", "c"])
        line_cache.store("/tmp/test.py", lines)

        cached = line_cache.get("/tmp/test.py")
        assert cached is not None
        assert len(cached) == 3
        assert cached[1].content == "a"
        assert cached[2].content == "b"
        assert cached[3].content == "c"

    def test_get_returns_read_only_view(self) -> None:
        lines = _make_lines(["a"])
        line_cache.store("/tmp/test.py", lines)

        cached = line_cache.get("/tmp/test.py")
        assert cached is not None

        with pytest.raises(TypeError):
            cached[1] = HashedLine(line_number=1, hash="00", content="x")  # type: ignore[index]

    def test_get_uncached_returns_none(self) -> None:
        assert line_cache.get("/nonexistent") is None

    def test_store_replaces_previous(self) -> None:
        lines_v1 = _make_lines(["old"])
        lines_v2 = _make_lines(["new"])
        line_cache.store("/tmp/f.py", lines_v1)
        line_cache.store("/tmp/f.py", lines_v2)

        cached = line_cache.get("/tmp/f.py")
        assert cached is not None
        assert cached[1].content == "new"


class TestGetLine:
    def test_get_existing_line(self) -> None:
        lines = _make_lines(["x", "y"])
        line_cache.store("/tmp/f.py", lines)

        hl = line_cache.get_line("/tmp/f.py", 2)
        assert hl is not None
        assert hl.content == "y"

    def test_get_missing_line(self) -> None:
        lines = _make_lines(["x"])
        line_cache.store("/tmp/f.py", lines)

        assert line_cache.get_line("/tmp/f.py", 99) is None

    def test_get_line_uncached_file(self) -> None:
        assert line_cache.get_line("/nope", 1) is None


class TestValidateRef:
    def test_valid_ref(self) -> None:
        lines = _make_lines(["hello world"])
        line_cache.store("/tmp/f.py", lines)

        h = content_hash("hello world")
        assert line_cache.validate_ref("/tmp/f.py", 1, h) is True

    def test_wrong_hash(self) -> None:
        lines = _make_lines(["hello world"])
        line_cache.store("/tmp/f.py", lines)

        assert line_cache.validate_ref("/tmp/f.py", 1, "zz") is False

    def test_uncached_file(self) -> None:
        assert line_cache.validate_ref("/nope", 1, "ab") is False

    def test_missing_line(self) -> None:
        lines = _make_lines(["x"])
        line_cache.store("/tmp/f.py", lines)

        assert line_cache.validate_ref("/tmp/f.py", 99, "ab") is False


class TestUpdateLines:
    def test_update_single_line(self) -> None:
        lines = _make_lines(["original"])
        line_cache.store("/tmp/f.py", lines)

        line_cache.update_lines("/tmp/f.py", {1: "updated"})

        hl = line_cache.get_line("/tmp/f.py", 1)
        assert hl is not None
        assert hl.content == "updated"
        assert hl.hash == content_hash("updated")

    def test_update_uncached_raises_runtime_error(self) -> None:
        with pytest.raises(RuntimeError, match="update_lines called for uncached file"):
            line_cache.update_lines("/nope", {1: "x"})


class TestReplaceRange:
    def test_replace_same_count(self) -> None:
        lines = _make_lines(["a", "b", "c"])
        line_cache.store("/tmp/f.py", lines)

        line_cache.replace_range("/tmp/f.py", 2, 2, ["B"])

        hl = line_cache.get_line("/tmp/f.py", 2)
        assert hl is not None
        assert hl.content == "B"
        # Lines 1 and 3 unchanged
        assert line_cache.get_line("/tmp/f.py", 1) is not None
        assert line_cache.get_line("/tmp/f.py", 3) is not None

    def test_replace_fewer_lines(self) -> None:
        lines = _make_lines(["a", "b", "c", "d"])
        line_cache.store("/tmp/f.py", lines)

        # Replace lines 2-3 with a single line
        line_cache.replace_range("/tmp/f.py", 2, 3, ["X"])

        # Line 1 unchanged
        assert line_cache.get_line("/tmp/f.py", 1) is not None
        assert line_cache.get_line("/tmp/f.py", 1).content == "a"  # type: ignore[union-attr]
        # Line 2 is the replacement
        assert line_cache.get_line("/tmp/f.py", 2) is not None
        assert line_cache.get_line("/tmp/f.py", 2).content == "X"  # type: ignore[union-attr]
        # Old line 4 shifted to line 3
        assert line_cache.get_line("/tmp/f.py", 3) is not None
        assert line_cache.get_line("/tmp/f.py", 3).content == "d"  # type: ignore[union-attr]

    def test_replace_more_lines(self) -> None:
        lines = _make_lines(["a", "b", "c"])
        line_cache.store("/tmp/f.py", lines)

        # Replace line 2 with two lines
        line_cache.replace_range("/tmp/f.py", 2, 2, ["X", "Y"])

        assert line_cache.get_line("/tmp/f.py", 2) is not None
        assert line_cache.get_line("/tmp/f.py", 2).content == "X"  # type: ignore[union-attr]
        assert line_cache.get_line("/tmp/f.py", 3) is not None
        assert line_cache.get_line("/tmp/f.py", 3).content == "Y"  # type: ignore[union-attr]
        # Old line 3 shifted to line 4
        assert line_cache.get_line("/tmp/f.py", 4) is not None
        assert line_cache.get_line("/tmp/f.py", 4).content == "c"  # type: ignore[union-attr]

    def test_replace_range_uncached_raises_runtime_error(self) -> None:
        with pytest.raises(RuntimeError, match="replace_range called for uncached file"):
            line_cache.replace_range("/nope", 1, 2, ["x"])


class TestInvalidateAndClear:
    def test_invalidate(self) -> None:
        lines = _make_lines(["x"])
        line_cache.store("/tmp/f.py", lines)
        line_cache.invalidate("/tmp/f.py")
        assert line_cache.get("/tmp/f.py") is None

    def test_invalidate_uncached_is_noop(self) -> None:
        line_cache.invalidate("/nope")

    def test_clear(self) -> None:
        line_cache.store("/tmp/a.py", _make_lines(["a"]))
        line_cache.store("/tmp/b.py", _make_lines(["b"]))
        line_cache.clear()
        assert line_cache.cached_files() == []

    def test_cached_files(self) -> None:
        line_cache.store("/tmp/a.py", _make_lines(["a"]))
        line_cache.store("/tmp/b.py", _make_lines(["b"]))
        assert sorted(line_cache.cached_files()) == ["/tmp/a.py", "/tmp/b.py"]
