"""Characterization tests for file operations and path handling in file_utils.py."""

import pytest
import sys
from tunacode.utils import file_utils

def test_dotdict_basic_access():
    d = file_utils.DotDict({'a': 1, 'b': 2})
    assert d.a == 1
    assert d['b'] == 2
    d.c = 3
    assert d['c'] == 3
    del d.a
    assert 'a' not in d

def test_dotdict_attribute_error():
    d = file_utils.DotDict()
    assert d.get('missing') is None
    # Current behavior: DotDict.__getattr__ uses dict.get, returns None instead of raising
    assert d.missing is None  # No AttributeError raised

def test_capture_stdout_captures_print():
    with file_utils.capture_stdout() as out:
        print("hello world")
    assert "hello world" in out.getvalue()

def test_capture_stdout_restores_sys_stdout():
    original = sys.stdout
    with file_utils.capture_stdout():
        pass
    assert sys.stdout is original