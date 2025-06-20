import pytest
import sys
import types

@pytest.fixture(autouse=True)
def cleanup_modules():
    """Automatically restore sys.modules after each test."""
    originals = {
        'tunacode.cli.main': sys.modules.get('tunacode.cli.main'),
        'tunacode.ui.console': sys.modules.get('tunacode.ui.console')
    }
    yield
    for name, original in originals.items():
        if original is not None:
            sys.modules[name] = original
        else:
            sys.modules.pop(name, None)

# Avoid importing full CLI app
sys.modules['tunacode.cli.main'] = types.SimpleNamespace(app=None)
sys.modules['tunacode.ui.console'] = types.SimpleNamespace()
from tunacode.cli.repl import _parse_args
from tunacode.exceptions import ValidationError


def test_parse_args_from_json():
    assert _parse_args('{"a": 1}') == {'a': 1}


def test_parse_args_from_dict():
    assert _parse_args({'x': 2}) == {'x': 2}


def test_parse_args_invalid():
    with pytest.raises(ValidationError):
        _parse_args('invalid')
