from __future__ import annotations

from pathlib import Path

from tunacode.configuration.ignore_patterns import DEFAULT_IGNORE_PATTERNS

from tunacode.infrastructure.file_filter import FileFilter


def _write_file(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_file_filter_complete_respects_default_and_gitignore_patterns(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("generated.txt\nignored-dir/\n", encoding="utf-8")
    _write_file(tmp_path / "src" / "app.py")
    _write_file(tmp_path / "docs" / "notes.md")
    _write_file(tmp_path / ".venv" / "ignored.py")
    _write_file(tmp_path / "generated.txt")
    _write_file(tmp_path / "ignored-dir" / "skip.py")

    file_filter = FileFilter(
        ignore_patterns=DEFAULT_IGNORE_PATTERNS,
        result_limit=20,
        max_depth=5,
        root=tmp_path,
    )
    results = file_filter.complete("")

    assert "src/app.py" in results
    assert "docs/notes.md" in results
    assert "generated.txt" not in results
    assert ".venv/" not in results
    assert ".venv/ignored.py" not in results
    assert "ignored-dir/" not in results
    assert "ignored-dir/skip.py" not in results


def test_file_filter_complete_falls_back_when_gitignore_is_invalid_utf8(
    tmp_path: Path,
) -> None:
    (tmp_path / ".gitignore").write_bytes(b"\xff\xfeignored-dir/\n")
    _write_file(tmp_path / "src" / "app.py")
    _write_file(tmp_path / "docs" / "notes.md")
    _write_file(tmp_path / ".venv" / "ignored.py")

    file_filter = FileFilter(
        ignore_patterns=DEFAULT_IGNORE_PATTERNS,
        result_limit=20,
        max_depth=5,
        root=tmp_path,
    )
    results = file_filter.complete("")

    assert "src/app.py" in results
    assert "docs/notes.md" in results
    assert ".venv/" not in results
    assert ".venv/ignored.py" not in results
