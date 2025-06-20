import sys
import types
import pytest
from importlib import reload

# Avoid importing heavy CLI main module when importing tool_ui
sys.modules['tunacode.cli.main'] = types.SimpleNamespace(app=None)
@pytest.fixture(autouse=True)
def cleanup_modules():
    """Automatically restore sys.modules after each test."""
    original = sys.modules.get('tunacode.ui.console')
    yield
    if original is not None:
        sys.modules['tunacode.ui.console'] = original
    else:
        sys.modules.pop('tunacode.ui.console', None)

sys.modules['tunacode.ui.console'] = types.SimpleNamespace()

import pytest

from tunacode.utils.bm25 import BM25, tokenize
from tunacode.utils.token_counter import estimate_tokens
from tunacode.ui.tool_ui import ToolUI


def test_bm25_scoring():
    docs = ['the cat sat on the mat', 'dogs and cats', 'the quick brown fox']
    bm25 = BM25(docs)
    scores = bm25.get_scores(tokenize('cat'))
    assert scores[0] > scores[1] >= 0


def test_token_counter():
    assert estimate_tokens('hello world') == len('hello world') // 4


def test_tool_ui_get_tool_title():
    ui = ToolUI()
    assert ui._get_tool_title('read_file').startswith('Tool')
    assert ui._get_tool_title('custom').startswith('MCP')


def test_render_file_diff(monkeypatch):
    # patch rich.text before import
    dummy_module = types.ModuleType('rich.text')
    class DummyText:
        def __init__(self):
            self.lines = []
        def append(self, text, style=None):
            self.lines.append(text)
    dummy_module.Text = DummyText
    monkeypatch.setitem(sys.modules, 'rich.text', dummy_module)
    from tunacode.utils import diff_utils
    reload(diff_utils)
    res = diff_utils.render_file_diff('a', 'b')
    assert isinstance(res, DummyText)
    assert any(line.startswith('- ') or line.startswith('+ ') for line in res.lines)
