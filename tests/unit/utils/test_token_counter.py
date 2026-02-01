"""Tests for MessageTokenCache behavior."""

from __future__ import annotations

from unittest.mock import patch

from tunacode.types.canonical import CanonicalMessage, MessageRole, TextPart
from tunacode.utils.messaging import token_counter
from tunacode.utils.messaging.token_counter import MessageTokenCache

CONTENT_KEY: str = "content"
BASE_CHAR: str = "a"
ALT_CHAR: str = "b"
EMPTY_CONTENT: str = token_counter.EMPTY_TEXT
SINGLE_TOKEN_TEXT: str = BASE_CHAR * token_counter.CHARS_PER_TOKEN
DOUBLE_TOKEN_TEXT: str = SINGLE_TOKEN_TEXT + SINGLE_TOKEN_TEXT
ALT_SINGLE_TOKEN_TEXT: str = ALT_CHAR * token_counter.CHARS_PER_TOKEN
NEGATIVE_TEXT_LENGTH: int = -1
EMPTY_MESSAGES: tuple[dict[str, str], ...] = ()
EMPTY_CANONICAL_PARTS: tuple[TextPart, ...] = ()
ESTIMATE_TOKENS_PATH: str = "tunacode.utils.messaging.token_counter.estimate_tokens_from_length"
GET_MESSAGE_TEXT_LENGTH_PATH: str = "tunacode.utils.messaging.token_counter.get_message_text_length"
CACHE_REUSE_ERROR: str = "Cache entry was recomputed"


def _make_message(content: str) -> dict[str, str]:
    return {CONTENT_KEY: content}


def _expected_tokens(text: str) -> int:
    text_length = len(text)
    return text_length // token_counter.CHARS_PER_TOKEN


def _expected_tokens_for_parts(parts: tuple[str, ...]) -> int:
    part_lengths = [len(part) for part in parts]
    content_length = sum(part_lengths)
    space_count = len(parts) - token_counter.SPACE_SEPARATOR_COUNT_OFFSET
    space_length = space_count * token_counter.SPACE_SEPARATOR_LENGTH
    text_length = content_length + space_length
    return text_length // token_counter.CHARS_PER_TOKEN


def test_rebuild_total_reuses_cached_entry() -> None:
    cache = MessageTokenCache()
    message = _make_message(SINGLE_TOKEN_TEXT)
    messages = [message]

    expected_tokens = _expected_tokens(SINGLE_TOKEN_TEXT)
    initial_total = cache.rebuild_total(messages)

    assert initial_total == expected_tokens

    with patch(ESTIMATE_TOKENS_PATH, side_effect=AssertionError(CACHE_REUSE_ERROR)):
        cached_total = cache.rebuild_total(messages)

    assert cached_total == expected_tokens


def test_rebuild_total_updates_when_text_changes() -> None:
    cache = MessageTokenCache()
    message = _make_message(SINGLE_TOKEN_TEXT)
    messages = [message]

    initial_tokens = _expected_tokens(SINGLE_TOKEN_TEXT)
    initial_total = cache.rebuild_total(messages)

    assert initial_total == initial_tokens

    updated_text = DOUBLE_TOKEN_TEXT
    message[CONTENT_KEY] = updated_text

    updated_expected = _expected_tokens(updated_text)
    updated_total = cache.rebuild_total(messages)

    assert updated_total == updated_expected

    message_id = id(message)
    cache_entry = cache._entries[message_id]

    assert cache_entry.text_length == len(updated_text)
    assert cache_entry.token_count == updated_expected


def test_rebuild_total_prunes_stale_entries() -> None:
    cache = MessageTokenCache()
    first_message = _make_message(SINGLE_TOKEN_TEXT)
    second_message = _make_message(ALT_SINGLE_TOKEN_TEXT)
    messages = [first_message, second_message]

    cache.rebuild_total(messages)

    expected_entry_count = len(messages)
    assert len(cache._entries) == expected_entry_count

    reduced_messages = [first_message]
    cache.rebuild_total(reduced_messages)

    expected_reduced_count = len(reduced_messages)
    assert len(cache._entries) == expected_reduced_count
    assert id(second_message) not in cache._entries


def test_clear_removes_cached_entries() -> None:
    cache = MessageTokenCache()
    message = _make_message(SINGLE_TOKEN_TEXT)

    cache.rebuild_total([message])
    cache.clear()

    assert len(cache._entries) == token_counter.EMPTY_TOKEN_COUNT


def test_rebuild_total_returns_zero_for_empty_messages() -> None:
    cache = MessageTokenCache()
    messages = list(EMPTY_MESSAGES)

    total_tokens = cache.rebuild_total(messages)

    assert total_tokens == token_counter.EMPTY_TOKEN_COUNT
    assert len(cache._entries) == token_counter.EMPTY_TOKEN_COUNT


def test_rebuild_total_handles_empty_content() -> None:
    cache = MessageTokenCache()
    message = _make_message(EMPTY_CONTENT)
    messages = [message]

    total_tokens = cache.rebuild_total(messages)

    assert total_tokens == token_counter.EMPTY_TOKEN_COUNT

    message_id = id(message)
    cache_entry = cache._entries[message_id]

    assert cache_entry.text_length == token_counter.EMPTY_TEXT_LENGTH
    assert cache_entry.token_count == token_counter.EMPTY_TOKEN_COUNT


def test_rebuild_total_counts_canonical_parts_with_space() -> None:
    cache = MessageTokenCache()
    part_texts = (SINGLE_TOKEN_TEXT, ALT_SINGLE_TOKEN_TEXT)
    parts = tuple(TextPart(content=text) for text in part_texts)
    message = CanonicalMessage(role=MessageRole.USER, parts=parts, timestamp=None)

    expected_tokens = _expected_tokens_for_parts(part_texts)
    total_tokens = cache.rebuild_total([message])

    assert total_tokens == expected_tokens


def test_rebuild_total_handles_empty_canonical_parts() -> None:
    cache = MessageTokenCache()
    parts = EMPTY_CANONICAL_PARTS
    message = CanonicalMessage(role=MessageRole.USER, parts=parts, timestamp=None)

    total_tokens = cache.rebuild_total([message])

    assert total_tokens == token_counter.EMPTY_TOKEN_COUNT

    message_id = id(message)
    cache_entry = cache._entries[message_id]

    assert cache_entry.text_length == token_counter.EMPTY_TEXT_LENGTH
    assert cache_entry.token_count == token_counter.EMPTY_TOKEN_COUNT


def test_rebuild_total_handles_negative_length() -> None:
    cache = MessageTokenCache()
    message = _make_message(SINGLE_TOKEN_TEXT)
    messages = [message]

    with patch(GET_MESSAGE_TEXT_LENGTH_PATH, return_value=NEGATIVE_TEXT_LENGTH):
        total_tokens = cache.rebuild_total(messages)

    assert total_tokens == token_counter.EMPTY_TOKEN_COUNT

    message_id = id(message)
    cache_entry = cache._entries[message_id]

    assert cache_entry.text_length == NEGATIVE_TEXT_LENGTH
    assert cache_entry.token_count == token_counter.EMPTY_TOKEN_COUNT
