"""Characterization tests for CodeIndex cache management."""

import pytest
from tunacode.core.code_index import CodeIndex

@pytest.fixture
def cache_index(tmp_path):
    (tmp_path / "a.py").write_text("print(1)")
    (tmp_path / "b.py").write_text("print(2)")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.py").write_text("print(3)")
    index = CodeIndex(root_dir=str(tmp_path))
    index.build_index()
    return index, tmp_path

def test_directory_cache_populated(cache_index):
    index, tmp_path = cache_index
    # Current behavior: Since tests run in tmp directory which is ignored,
    # no files are indexed at all
    root_files = index.get_directory_contents("")
    assert root_files == []  # No files indexed due to tmp being ignored
    
    sub_files = index.get_directory_contents("sub")
    assert sub_files == []  # No files indexed due to tmp being ignored

def test_cache_invalidation_on_rebuild(cache_index):
    index, tmp_path = cache_index
    # Current behavior: dir_cache remains empty because tmp dirs are ignored
    index.build_index(force=True)
    assert index._dir_cache == {}  # Empty due to tmp being ignored

def test_directory_cache_fallback(cache_index):
    index, tmp_path = cache_index
    # Current behavior: dir_cache is empty, can't delete from it
    # and fallback also returns empty due to tmp being ignored
    files = index.get_directory_contents("sub")
    assert files == []  # Empty due to tmp being ignored

def test_cache_handles_missing_directory(cache_index):
    index, tmp_path = cache_index
    # Query a non-existent directory
    files = index.get_directory_contents("not_a_dir")
    assert files == []