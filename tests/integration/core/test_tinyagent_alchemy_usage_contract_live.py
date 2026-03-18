from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, cast

import pytest
from tinyagent.agent_types import Context, SimpleStreamOptions, TextContent, UserMessage
from tinyagent.alchemy_provider import OpenAICompatModel, stream_alchemy_openai_completions

CHUTES_API_KEY_ENV = "CHUTES_API_KEY"
CHUTES_CHAT_COMPLETIONS_URL = "https://llm.chutes.ai/v1/chat/completions"
CHUTES_TEST_MODEL_ID = "deepseek-ai/DeepSeek-V3.1"
LIVE_PROMPT_TEXT = "Reply with exactly: OK"
LIVE_SYSTEM_PROMPT = "Respond with exactly OK."
STREAM_TIMEOUT_SECONDS = 90
LIVE_MAX_TOKENS = 32
DOTENV_FILE = ".env"
ENV_COMMENT_PREFIX = "#"
ENV_ASSIGNMENT_SEPARATOR = "="
EXPECTED_USAGE_KEYS = frozenset(
    {"input", "output", "cache_read", "cache_write", "total_tokens", "cost"}
)
EXPECTED_COST_KEYS = frozenset({"input", "output", "cache_read", "cache_write", "total"})


def _read_dotenv_value(key: str) -> str | None:
    dotenv_path = Path(DOTENV_FILE)
    if not dotenv_path.exists():
        return None

    key_prefix = f"{key}{ENV_ASSIGNMENT_SEPARATOR}"
    for raw_line in dotenv_path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(ENV_COMMENT_PREFIX):
            continue
        if not line.startswith(key_prefix):
            continue

        raw_value = line[len(key_prefix) :].strip()
        if not raw_value:
            return None

        normalized_value = raw_value.strip("\"'")
        if not normalized_value:
            return None
        return normalized_value

    return None


def _has_working_alchemy_binding() -> bool:
    try:
        import tinyagent._alchemy  # noqa: F401
    except Exception:
        return False
    return True


CHUTES_API_KEY = os.environ.get(CHUTES_API_KEY_ENV) or _read_dotenv_value(CHUTES_API_KEY_ENV)
HAS_ALCHEMY_BINDING = _has_working_alchemy_binding()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not CHUTES_API_KEY or not HAS_ALCHEMY_BINDING,
    reason=(
        "Requires CHUTES_API_KEY in env or .env and a working tinyagent._alchemy binding "
        "for live alchemy usage contract test"
    ),
)
async def test_tinyagent_alchemy_result_includes_canonical_usage_contract() -> None:
    model = OpenAICompatModel(
        provider="chutes",
        id=CHUTES_TEST_MODEL_ID,
        base_url=CHUTES_CHAT_COMPLETIONS_URL,
        headers={"X-Title": "tunacode-live-alchemy-usage-contract-test"},
    )
    context = Context(
        system_prompt=LIVE_SYSTEM_PROMPT,
        messages=[
            UserMessage(
                content=[
                    TextContent(text=LIVE_PROMPT_TEXT),
                ],
            )
        ],
        tools=None,
    )

    stream_options = SimpleStreamOptions(
        api_key=CHUTES_API_KEY,
        max_tokens=LIVE_MAX_TOKENS,
    )
    response = await asyncio.wait_for(
        stream_alchemy_openai_completions(model, context, stream_options),
        timeout=STREAM_TIMEOUT_SECONDS,
    )

    saw_done_event = False
    saw_error_event = False
    async for event in response:
        if event.type == "done":
            saw_done_event = True
        if event.type == "error":
            saw_error_event = True

    final_message = await asyncio.wait_for(response.result(), timeout=STREAM_TIMEOUT_SECONDS)
    if saw_error_event:
        error_message = getattr(final_message, "error_message", None)
        if isinstance(error_message, str) and error_message:
            pytest.skip(f"Live provider unavailable: {error_message}")
        pytest.skip("Live provider returned an error event")

    assert saw_done_event

    usage_raw = final_message.usage
    assert isinstance(usage_raw, dict)

    missing_usage_keys = EXPECTED_USAGE_KEYS.difference(usage_raw.keys())
    assert not missing_usage_keys

    assert "prompt_tokens" not in usage_raw
    assert "completion_tokens" not in usage_raw
    assert "cacheRead" not in usage_raw

    usage = cast(dict[str, Any], usage_raw)
    for key in ("input", "output", "cache_read", "cache_write", "total_tokens"):
        value = usage.get(key)
        assert isinstance(value, int)
        assert value >= 0

    cost_raw = usage.get("cost")
    assert isinstance(cost_raw, dict)

    missing_cost_keys = EXPECTED_COST_KEYS.difference(cost_raw.keys())
    assert not missing_cost_keys

    cost = cast(dict[str, Any], cost_raw)
    for key in EXPECTED_COST_KEYS:
        value = cost.get(key)
        assert isinstance(value, int | float)
        assert float(value) >= 0.0
