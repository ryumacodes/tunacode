from __future__ import annotations

from tinyagent.agent_types import (
    ZERO_USAGE,
    AssistantMessage,
    AssistantMessageEvent,
    TextContent,
)

MINIMAX_CODING_PLAN_MODEL = "minimax-coding-plan:MiniMax-M2.1"
MINIMAX_API_KEY_ENV = "MINIMAX_API_KEY"
MINIMAX_API_KEY_VALUE = "sk-minimax"
MINIMAX_CHAT_COMPLETIONS_URL = "https://api.minimax.io/v1/chat/completions"
MINIMAX_ALCHEMY_API = "minimax-completions"


class _FakeResponse:
    def __init__(self) -> None:
        self._done_emitted = False

    def __aiter__(self) -> _FakeResponse:
        return self

    async def __anext__(self) -> AssistantMessageEvent:
        if self._done_emitted:
            raise StopAsyncIteration

        self._done_emitted = True
        return AssistantMessageEvent(type="done")

    async def result(self) -> AssistantMessage:
        return AssistantMessage(
            content=[TextContent(text="ok")],
            stop_reason="stop",
            provider="minimax-coding-plan",
            model="MiniMax-M2.1",
            usage=ZERO_USAGE,
        )
