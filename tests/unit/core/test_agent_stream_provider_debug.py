from __future__ import annotations

from dataclasses import dataclass, field

from tinyagent.agent_types import AssistantMessage, AssistantMessageEvent, SimpleStreamOptions

from tunacode.core.agents.agent_components import agent_config


@dataclass
class _FakeLogger:
    messages: list[str] = field(default_factory=list)
    debug_mode: bool = True

    def lifecycle(self, message: str) -> None:
        self.messages.append(message)

    def warning(self, message: str, **_kwargs: object) -> None:
        self.messages.append(message)


class _FakeResponse:
    def __init__(self) -> None:
        self._events = [
            AssistantMessageEvent(type="start"),
            AssistantMessageEvent(type="text_delta", delta="hi"),
        ]

    def __aiter__(self) -> _FakeResponse:
        return self

    async def __anext__(self) -> AssistantMessageEvent:
        if not self._events:
            raise StopAsyncIteration
        return self._events.pop(0)

    async def result(self) -> AssistantMessage:
        return AssistantMessage(content=[])


async def test_build_stream_fn_wraps_provider_response_with_debug_tracing(
    monkeypatch,
) -> None:
    logger = _FakeLogger()
    fake_response = _FakeResponse()

    async def _fake_stream_alchemy_openai_completions(
        model: object,
        context: object,
        options: SimpleStreamOptions,
    ) -> _FakeResponse:
        _ = (model, context, options)
        return fake_response

    monkeypatch.setattr(agent_config, "get_logger", lambda: logger)
    monkeypatch.setattr(
        agent_config,
        "stream_alchemy_openai_completions",
        _fake_stream_alchemy_openai_completions,
    )

    perf_counter_values = iter([100.0, 100.2, 100.6, 101.0, 101.1, 101.3])
    monkeypatch.setattr(agent_config.time, "perf_counter", lambda: next(perf_counter_values))

    stream_fn = agent_config._build_stream_fn(request_delay=0.0, max_tokens=None, max_retries=1)
    response = await stream_fn(model=object(), context=object(), options=SimpleStreamOptions())

    first_event = await response.__anext__()
    second_event = await response.__anext__()
    result = await response.result()

    assert first_event.type == "start"
    assert second_event.type == "text_delta"
    assert isinstance(result, AssistantMessage)
    assert logger.messages[0] == "Stream: provider_open attempt=1/1 dur=200.0ms"
    assert (
        logger.messages[1]
        == "Stream: provider_first_raw type=start since_open=600.0ms since_response=400.0ms"
    )
    assert logger.messages[2] == "Stream: provider_raw_gap type=text_delta gap=400.0ms count=2"
    assert logger.messages[3] == "Stream: provider_result dur=200.0ms"
