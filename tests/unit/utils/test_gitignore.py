from __future__ import annotations

from pathlib import Path

from tunacode.utils.system.gitignore import list_cwd


def _write_file(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_list_cwd_respects_shared_ignore_rules(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("generated.txt\nignored-dir/\n", encoding="utf-8")
    _write_file(tmp_path / "src" / "app.py")
    _write_file(tmp_path / "docs" / "notes.md")
    _write_file(tmp_path / ".venv" / "ignored.py")
    _write_file(tmp_path / "generated.txt")
    _write_file(tmp_path / "ignored-dir" / "skip.py")

    results = list_cwd(max_depth=5)

    assert "src/app.py" in results
    assert "docs/notes.md" in results
    assert "generated.txt" not in results
    assert ".venv/ignored.py" not in results
    assert "ignored-dir/skip.py" not in results


def test_list_cwd_falls_back_when_gitignore_is_unreadable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    original_read_text = Path.read_text

    def _raise_permission_error(self: Path, *args, **kwargs) -> str:
        if self == tmp_path / ".gitignore":
            raise PermissionError("permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("generated.txt\n", encoding="utf-8")
    _write_file(tmp_path / "src" / "app.py")
    _write_file(tmp_path / ".venv" / "ignored.py")
    monkeypatch.setattr(Path, "read_text", _raise_permission_error)

    results = list_cwd(max_depth=5)

    assert "src/app.py" in results
    assert ".venv/ignored.py" not in results


def test_list_cwd_falls_back_when_gitignore_is_a_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").mkdir()
    _write_file(tmp_path / "src" / "app.py")
    _write_file(tmp_path / ".venv" / "ignored.py")

    results = list_cwd(max_depth=5)

    assert "src/app.py" in results
    assert ".venv/ignored.py" not in results
