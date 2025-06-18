"""Characterization tests for token counting utilities in token_counter.py."""

import pytest
from tunacode.utils import token_counter

@pytest.mark.parametrize("text,expected", [
    ("", 0),
    ("abcd", 1),
    ("abcdefgh", 2),
    ("a" * 100, 25),
    ("hello world", 2),
    ("    ", 1),
    ("a" * 3999, 999),
    ("a" * 4000, 1000),
])
def test_estimate_tokens_various_lengths(text, expected):
    assert token_counter.estimate_tokens(text) == expected

def test_estimate_tokens_none():
    assert token_counter.estimate_tokens("") == 0

@pytest.mark.parametrize("count,expected", [
    (0, "0"),
    (999, "999"),
    (1000, "1,000"),
    (1234567, "1,234,567"),
])
def test_format_token_count(count, expected):
    assert token_counter.format_token_count(count) == expected