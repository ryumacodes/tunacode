"""Tests for the hashline content-hashing utility."""

import hashlib

import pytest

from tunacode.tools.hashline import (
    HASH_LENGTH,
    HashedLine,
    content_hash,
    format_hashline,
    format_hashlines,
    parse_line_ref,
    tag_lines,
)


class TestContentHash:
    def test_returns_two_hex_chars(self) -> None:
        result = content_hash("hello")
        assert len(result) == HASH_LENGTH
        # Must be valid hex
        int(result, 16)

    def test_deterministic(self) -> None:
        assert content_hash("test") == content_hash("test")

    def test_matches_md5_prefix(self) -> None:
        line = "function hello() {"
        expected = hashlib.md5(line.encode(), usedforsecurity=False).hexdigest()[:HASH_LENGTH]
        assert content_hash(line) == expected

    def test_different_content_usually_different_hash(self) -> None:
        h1 = content_hash("aaa")
        h2 = content_hash("bbb")
        assert h1 != h2
        assert len(h1) == HASH_LENGTH
        assert len(h2) == HASH_LENGTH

    def test_empty_line(self) -> None:
        result = content_hash("")
        assert len(result) == HASH_LENGTH


class TestTagLines:
    def test_basic_tagging(self) -> None:
        content = "line one\nline two\nline three"
        tagged = tag_lines(content)

        assert len(tagged) == 3
        assert tagged[0].line_number == 1
        assert tagged[0].content == "line one"
        assert tagged[1].line_number == 2
        assert tagged[2].line_number == 3

    def test_offset(self) -> None:
        content = "line one\nline two"
        tagged = tag_lines(content, offset=10)

        assert tagged[0].line_number == 11
        assert tagged[1].line_number == 12

    def test_single_line(self) -> None:
        tagged = tag_lines("only line")
        assert len(tagged) == 1
        assert tagged[0].line_number == 1
        assert tagged[0].content == "only line"

    def test_empty_content(self) -> None:
        tagged = tag_lines("")
        assert len(tagged) == 0

    def test_hashes_are_valid(self) -> None:
        tagged = tag_lines("a\nb\nc")
        for hl in tagged:
            assert len(hl.hash) == HASH_LENGTH
            assert hl.hash == content_hash(hl.content)


class TestFormatHashline:
    def test_format(self) -> None:
        hl = HashedLine(line_number=1, hash="a3", content="function hello() {")
        result = format_hashline(hl)
        assert result == "1:a3|function hello() {"

    def test_format_multidigit_line(self) -> None:
        hl = HashedLine(line_number=42, hash="ff", content="return true;")
        result = format_hashline(hl)
        assert result == "42:ff|return true;"

    def test_format_empty_content(self) -> None:
        hl = HashedLine(line_number=5, hash="d4", content="")
        result = format_hashline(hl)
        assert result == "5:d4|"


class TestFormatHashlines:
    def test_multiline(self) -> None:
        content = "a\nb\nc"
        result = format_hashlines(content)
        lines = result.split("\n")
        assert len(lines) == 3
        # Each line should match the pattern N:HH|content
        for line in lines:
            assert ":" in line
            assert "|" in line

    def test_with_offset(self) -> None:
        content = "x\ny"
        result = format_hashlines(content, offset=5)
        lines = result.split("\n")
        assert lines[0].startswith("6:")
        assert lines[1].startswith("7:")


class TestParseLineRef:
    def test_valid_ref(self) -> None:
        line_num, h = parse_line_ref("2:f1")
        assert line_num == 2
        assert h == "f1"

    def test_large_line_number(self) -> None:
        line_num, h = parse_line_ref("1000:ab")
        assert line_num == 1000
        assert h == "ab"

    def test_missing_separator(self) -> None:
        with pytest.raises(ValueError, match="expected format"):
            parse_line_ref("2f1")

    def test_non_numeric_line(self) -> None:
        with pytest.raises(ValueError, match="Invalid line number"):
            parse_line_ref("abc:f1")

    def test_wrong_hash_length(self) -> None:
        with pytest.raises(ValueError, match="Invalid hash length"):
            parse_line_ref("2:abc")

    def test_single_char_hash_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid hash length"):
            parse_line_ref("1:a")
