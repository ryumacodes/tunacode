"""Tests for tunacode.utils.system.gitignore."""

import os
from unittest.mock import patch

from tunacode.utils.system.gitignore import _load_gitignore_patterns, list_cwd


class TestLoadGitignorePatterns:
    def test_loads_patterns_from_file(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\nnode_modules/\n# comment\n\n__pycache__/\n")

        patterns = _load_gitignore_patterns(str(gitignore))
        assert patterns is not None
        assert "*.pyc" in patterns
        assert "node_modules/" in patterns
        assert "__pycache__/" in patterns
        # Comments and blank lines should be excluded
        assert "# comment" not in patterns
        assert "" not in patterns

    def test_always_includes_git_dir(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")
        patterns = _load_gitignore_patterns(str(gitignore))
        assert patterns is not None
        assert ".git/" in patterns

    def test_returns_none_for_missing_file(self):
        result = _load_gitignore_patterns("/nonexistent/.gitignore")
        assert result is None

    def test_returns_none_on_read_error(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("content")
        with patch("builtins.open", side_effect=OSError("read error")):
            result = _load_gitignore_patterns(str(gitignore))
            assert result is None

class TestListCwd:
    def test_lists_files_in_directory(self, tmp_path):
        (tmp_path / "file1.py").write_text("a")
        (tmp_path / "file2.txt").write_text("b")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "file3.py").write_text("c")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = list_cwd(max_depth=3)
            assert isinstance(result, list)
            assert result == sorted(result)
            assert "file1.py" in result
            assert "file2.txt" in result
        finally:
            os.chdir(original_cwd)

    def test_max_depth_zero_only_top_level(self, tmp_path):
        (tmp_path / "top.py").write_text("a")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.py").write_text("b")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = list_cwd(max_depth=0)
            for f in result:
                assert "/" not in f, f"Expected no nested files, got: {f}"
        finally:
            os.chdir(original_cwd)

    def test_returns_sorted_list(self, tmp_path):
        (tmp_path / "b.txt").write_text("")
        (tmp_path / "a.txt").write_text("")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = list_cwd(max_depth=0)
            assert result == sorted(result)
        finally:
            os.chdir(original_cwd)

    def test_negative_depth_treated_as_zero(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.txt").write_text("")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = list_cwd(max_depth=-1)
            for f in result:
                assert "/" not in f
        finally:
            os.chdir(original_cwd)
