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
