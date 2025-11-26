"""Tests for the fuzzy edit replacer strategies."""

import pytest

from tunacode.tools_utils.text_match import (
    block_anchor_replacer,
    indentation_flexible_replacer,
    levenshtein,
    line_trimmed_replacer,
    replace,
    simple_replacer,
)


class TestLevenshtein:
    """Tests for Levenshtein distance calculation."""

    def test_identical_strings(self):
        assert levenshtein("hello", "hello") == 0

    def test_empty_strings(self):
        assert levenshtein("", "") == 0
        assert levenshtein("abc", "") == 3
        assert levenshtein("", "xyz") == 3

    def test_single_char_difference(self):
        assert levenshtein("cat", "bat") == 1
        assert levenshtein("cat", "car") == 1

    def test_insertion_deletion(self):
        assert levenshtein("cat", "cats") == 1
        assert levenshtein("cats", "cat") == 1

    def test_complete_difference(self):
        assert levenshtein("abc", "xyz") == 3


class TestSimpleReplacer:
    """Tests for exact match replacer."""

    def test_exact_match(self):
        content = "hello world"
        find = "world"
        results = list(simple_replacer(content, find))
        assert results == ["world"]

    def test_no_match(self):
        content = "hello world"
        find = "foo"
        results = list(simple_replacer(content, find))
        assert results == []

    def test_multiline_match(self):
        content = "line1\nline2\nline3"
        find = "line2\nline3"
        results = list(simple_replacer(content, find))
        assert results == ["line2\nline3"]


class TestLineTrimmedReplacer:
    """Tests for whitespace-tolerant line matching."""

    def test_trailing_whitespace(self):
        content = "def foo():  \n    pass"
        find = "def foo():\n    pass"
        results = list(line_trimmed_replacer(content, find))
        assert len(results) == 1
        assert "def foo():" in results[0]

    def test_leading_whitespace(self):
        content = "  def foo():\n    pass"
        find = "def foo():\n    pass"
        results = list(line_trimmed_replacer(content, find))
        assert len(results) == 1

    def test_both_whitespace(self):
        content = "  hello world  \n  goodbye  "
        find = "hello world\ngoodbye"
        results = list(line_trimmed_replacer(content, find))
        assert len(results) == 1

    def test_no_match_different_content(self):
        content = "hello world\nfoo bar"
        find = "hello world\nbaz qux"
        results = list(line_trimmed_replacer(content, find))
        assert results == []

    def test_trailing_newline_in_find(self):
        content = "line1\nline2\nline3"
        find = "line1\nline2\n"  # Trailing newline
        results = list(line_trimmed_replacer(content, find))
        assert len(results) == 1


class TestIndentationFlexibleReplacer:
    """Tests for indentation-normalized matching."""

    def test_different_indentation_levels(self):
        content = "    def foo():\n        pass"
        find = "def foo():\n    pass"
        results = list(indentation_flexible_replacer(content, find))
        assert len(results) == 1
        # Should return the original indented version
        assert results[0] == "    def foo():\n        pass"

    def test_no_indentation_in_content(self):
        content = "def foo():\n    pass"
        find = "    def foo():\n        pass"
        results = list(indentation_flexible_replacer(content, find))
        assert len(results) == 1

    def test_matching_indentation(self):
        content = "def foo():\n    pass"
        find = "def foo():\n    pass"
        results = list(indentation_flexible_replacer(content, find))
        assert len(results) == 1

    def test_no_match_different_structure(self):
        content = "def foo():\n    pass"
        find = "def bar():\n    pass"
        results = list(indentation_flexible_replacer(content, find))
        assert results == []


class TestBlockAnchorReplacer:
    """Tests for anchor-based fuzzy matching."""

    def test_exact_anchors_fuzzy_middle(self):
        content = "def foo():\n    x = 1\n    y = 2\n    return x + y"
        # Same first/last lines, slightly different middle
        find = "def foo():\n    a = 1\n    b = 2\n    return x + y"
        results = list(block_anchor_replacer(content, find))
        # Should match based on anchors
        assert len(results) == 1

    def test_needs_minimum_lines(self):
        content = "line1\nline2"
        find = "line1\nline2"
        # Block anchor requires at least 3 lines
        results = list(block_anchor_replacer(content, find))
        assert results == []

    def test_no_matching_anchors(self):
        content = "def foo():\n    pass\n    return None"
        find = "def bar():\n    pass\n    return None"
        results = list(block_anchor_replacer(content, find))
        assert results == []

    def test_multiple_candidates_picks_best(self):
        content = """def foo():
    x = 1
    return x

def foo():
    x = 2
    return x"""
        # Should match the one with more similar middle
        find = "def foo():\n    x = 2\n    return x"
        results = list(block_anchor_replacer(content, find))
        assert len(results) == 1
        assert "x = 2" in results[0]


class TestReplace:
    """Tests for the main replace() function."""

    def test_exact_replacement(self):
        content = "hello world"
        result = replace(content, "world", "universe")
        assert result == "hello universe"

    def test_multiline_replacement(self):
        content = "def foo():\n    pass\n\ndef bar():\n    pass"
        result = replace(content, "def foo():\n    pass", "def foo():\n    return 42")
        assert "return 42" in result
        assert "def bar():" in result

    def test_whitespace_tolerant(self):
        content = "def foo():  \n    pass"
        # Find without trailing space
        result = replace(content, "def foo():\n    pass", "def foo():\n    return 1")
        assert "return 1" in result

    def test_indentation_tolerant(self):
        content = "    def foo():\n        pass"
        # Find with different indentation
        result = replace(content, "def foo():\n    pass", "def foo():\n    return 1")
        # Result should have the new content but preserve structure
        assert "return 1" in result

    def test_same_string_raises(self):
        with pytest.raises(ValueError, match="must be different"):
            replace("hello", "hello", "hello")

    def test_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            replace("hello world", "foo bar", "baz")

    def test_multiple_matches_raises(self):
        content = "foo bar foo"
        with pytest.raises(ValueError, match="multiple matches"):
            replace(content, "foo", "baz")

    def test_replace_all(self):
        content = "foo bar foo"
        result = replace(content, "foo", "baz", replace_all=True)
        assert result == "baz bar baz"

    def test_fuzzy_match_with_anchor(self):
        content = """def process():
    # Setup
    data = load()
    # Process
    result = transform(data)
    # Return
    return result"""

        # LLM might have slightly wrong middle content
        find = """def process():
    # Setup
    data = fetch()
    # Process
    result = transform(data)
    # Return
    return result"""

        # Should still match due to anchor matching
        result = replace(content, find, "def process():\n    return None")
        assert "return None" in result


class TestRealWorldScenarios:
    """Tests mimicking real agent edit scenarios."""

    def test_markdown_status_update(self):
        """The scenario from the screenshot - updating a markdown plan."""
        content = """# Plan

## Task 1
- [x] Done

## Task 2: Split Schema Tests
- [ ] IN PROGRESS

## Summary
50% complete
"""
        # Agent tries to mark task 2 as complete
        find = "## Task 2: Split Schema Tests\n- [ ] IN PROGRESS"
        replacement = "## Task 2: Split Schema Tests\n- [x] COMPLETED"

        result = replace(content, find, replacement)
        assert "COMPLETED" in result
        assert "IN PROGRESS" not in result

    def test_python_function_edit(self):
        """Editing a Python function with indentation differences."""
        content = """class Foo:
    def bar(self):
        x = 1
        y = 2
        return x + y
"""
        # Agent might provide without class indentation
        find = "def bar(self):\n    x = 1\n    y = 2\n    return x + y"
        replacement = "def bar(self):\n    return 3"

        result = replace(content, find, replacement)
        assert "return 3" in result

    def test_trailing_whitespace_mismatch(self):
        """Common issue: file has trailing whitespace, LLM doesn't include it."""
        content = "DEBUG = False  \nLOG_LEVEL = 'INFO'"
        find = "DEBUG = False\nLOG_LEVEL = 'INFO'"
        replacement = "DEBUG = True\nLOG_LEVEL = 'DEBUG'"

        result = replace(content, find, replacement)
        assert "DEBUG = True" in result
