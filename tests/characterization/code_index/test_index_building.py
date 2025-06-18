"""Characterization tests for CodeIndex index building."""

import pytest
from unittest.mock import patch, MagicMock
from tunacode.core.code_index import CodeIndex

@pytest.fixture
def mock_filesystem(tmp_path):
    # Create a fake directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import os\nclass Foo:\n    pass\ndef bar():\n    pass\n")
    (tmp_path / "README.md").write_text("# Project\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "src" / "ignore.me").write_text("should be ignored")
    return tmp_path

def test_index_builds_and_ignores_dirs(mock_filesystem):
    index = CodeIndex(root_dir=str(mock_filesystem))
    with patch.object(CodeIndex, "_scan_directory", wraps=index._scan_directory) as scan_mock:
        index.build_index()
        # Current behavior: Nothing is indexed because tmp path is ignored
        assert len(index._all_files) == 0  # No files indexed due to tmp
        # _scan_directory is still called at least once with root
        assert scan_mock.call_count >= 1

def test_force_rebuild(mock_filesystem):
    index = CodeIndex(root_dir=str(mock_filesystem))
    index.build_index()
    with patch.object(index, "_clear_indices") as clear_mock:
        index.build_index(force=True)
        clear_mock.assert_called_once()

def test_index_build_error(monkeypatch, mock_filesystem):
    # Simulate error in _scan_directory
    index = CodeIndex(root_dir=str(mock_filesystem))
    monkeypatch.setattr(index, "_scan_directory", lambda _: (_ for _ in ()).throw(Exception("fail")))
    with pytest.raises(Exception):
        index.build_index()

def test_index_thread_safety(mock_filesystem):
    # Ensure build_index uses a lock (simulate by patching threading.RLock)
    with patch("threading.RLock") as lock_mock:
        index = CodeIndex(root_dir=str(mock_filesystem))
        index.build_index()
        assert lock_mock.return_value.__enter__.called