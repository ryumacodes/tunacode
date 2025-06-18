"""Characterization tests for CodeIndex file scanning and filtering."""

import pytest
from unittest.mock import patch, MagicMock
from tunacode.core.code_index import CodeIndex

@pytest.fixture
def mock_file(tmp_path):
    def _create(name, content="", size=None):
        file = tmp_path / name
        file.write_text(content)
        if size:
            file.write_bytes(b"x" * size)
        return file
    return _create

def test_should_index_file_by_extension(tmp_path, mock_file):
    index = CodeIndex(root_dir=str(tmp_path))
    py = mock_file("foo.py", "print(1)")
    md = mock_file("README.md", "# doc")
    txt = mock_file("notes.txt", "note")
    exe = mock_file("run.exe", "")
    assert index._should_index_file(py)  # .py is indexed
    assert index._should_index_file(md)  # .md is indexed
    assert index._should_index_file(txt)  # .txt IS indexed
    assert not index._should_index_file(exe)  # .exe is NOT indexed

def test_should_index_file_shebang(tmp_path, mock_file):
    index = CodeIndex(root_dir=str(tmp_path))
    script = mock_file("myscript", "#!/bin/bash\necho hi")
    assert index._should_index_file(script)

def test_should_index_file_makefile(tmp_path, mock_file):
    index = CodeIndex(root_dir=str(tmp_path))
    makefile = mock_file("Makefile", "all:\n\techo hi")
    assert index._should_index_file(makefile)

def test_should_not_index_large_file(tmp_path, mock_file):
    index = CodeIndex(root_dir=str(tmp_path))
    big = mock_file("big.py", size=11 * 1024 * 1024)
    assert not index._should_index_file(big)

def test_should_ignore_hidden_and_ignored_dirs(tmp_path):
    index = CodeIndex(root_dir=str(tmp_path))
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    assert index._should_ignore_path(hidden)  # Hidden dirs are ignored
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    assert index._should_ignore_path(ignored)  # node_modules is ignored
    not_ignored = tmp_path / "src"
    not_ignored.mkdir()
    # Current behavior: Any path under tmp is ignored because 'tmp' is in IGNORE_DIRS
    assert index._should_ignore_path(not_ignored)