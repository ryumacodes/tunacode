"""Characterization tests for CodeIndex symbol extraction."""

import pytest
from tunacode.core.code_index import CodeIndex

@pytest.fixture
def pyfile(tmp_path):
    def _create(name, content):
        file = tmp_path / name
        file.write_text(content)
        return file
    return _create

def test_extracts_classes_and_functions(tmp_path, pyfile):
    code = '''
import os
from sys import path
class Foo:
    pass
class Bar(Baz):
    pass
def bar():
    pass
def _private():
    pass
'''
    f = pyfile("mod.py", code)
    index = CodeIndex(root_dir=str(tmp_path))
    index._index_python_file(f, f.relative_to(tmp_path))
    # Should extract both classes
    assert "Foo" in index._class_definitions
    assert "Bar" in index._class_definitions
    # Should extract both functions
    assert "bar" in index._function_definitions
    assert "_private" in index._function_definitions

def test_extracts_imports(tmp_path, pyfile):
    code = '''
import os
from sys import path
from foo.bar import baz
'''
    f = pyfile("mod.py", code)
    index = CodeIndex(root_dir=str(tmp_path))
    index._index_python_file(f, f.relative_to(tmp_path))
    rel = f.relative_to(tmp_path)
    # Should extract 'os', 'sys', 'foo'
    assert rel in index._path_to_imports
    imports = index._path_to_imports[rel]
    assert "os" in imports
    assert "sys" in imports
    assert "foo" in imports

def test_symbol_extraction_error_handling(tmp_path, pyfile, caplog):
    # Should not raise on bad file
    f = pyfile("bad.py", "\x00\x00\x00")
    index = CodeIndex(root_dir=str(tmp_path))
    # Current behavior: null bytes are handled fine, no error logged
    index._index_python_file(f, f.relative_to(tmp_path))
    # No symbols extracted from null bytes
    assert len(index._class_definitions) == 0
    assert len(index._function_definitions) == 0