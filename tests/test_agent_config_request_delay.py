"""Tests for agent HTTP client setup and request delay configuration."""

from __future__ import annotations

import copy

import httpx
import pytest
from pydantic_ai.retries import AsyncTenacityTransport

from tunacode.configuration.defaults import DEFAULT_USER_CONFIG
from tunacode.core.agents.agent_components import agent_config as ac
from tunacode.core.state import StateManager


@pytest.fixture(autouse=True)
def clear_agent_caches():
    """Ensure agent caches do not leak across tests."""
    ac.clear_all_caches()
    yield
    ac.clear_all_caches()


@pytest.fixture
def state_manager() -> StateManager:
    """Provide a fresh StateManager with default user config."""
    manager = StateManager()
    manager.session.user_config = copy.deepcopy(DEFAULT_USER_CONFIG)
    return manager


def test_request_delay_default_zero(state_manager: StateManager) -> None:
    """Request delay should default to zero (no throttling)."""
    assert state_manager.session.user_config["settings"]["request_delay"] == 0.0


@pytest.mark.asyncio
async def test_request_delay_hook_applies_sleep(
    monkeypatch: pytest.MonkeyPatch, state_manager: StateManager
) -> None:
    """Configure a request delay and ensure the HTTP client awaits it per request."""
    state_manager.session.user_config["settings"]["request_delay"] = 0.25
    captured_hooks: dict = {}

    class RecordingAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            captured_hooks.update(kwargs.get("event_hooks") or {})
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(ac, "AsyncClient", RecordingAsyncClient)
    monkeypatch.setattr(ac, "asyncio", __import__("asyncio"), raising=False)
    ac.get_or_create_agent("openai:gpt-4.1", state_manager)

    request_hooks = captured_hooks.get("request")
    assert request_hooks, "Expected a request hook to enforce request_delay"

    hook = request_hooks[0]
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(ac.asyncio, "sleep", fake_sleep)

    await hook(httpx.Request("GET", "http://example.com"))

    assert sleep_calls == [0.25]


def test_http_client_uses_retry_transport_by_default(
    monkeypatch: pytest.MonkeyPatch, state_manager: StateManager
) -> None:
    """Golden baseline: HTTP client uses retry transport without request hooks."""
    captured_kwargs: dict = {}

    class RecordingAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            captured_kwargs.update(kwargs)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(ac, "AsyncClient", RecordingAsyncClient)

    ac.get_or_create_agent("openai:gpt-4.1", state_manager)

    transport = captured_kwargs.get("transport")
    assert isinstance(transport, AsyncTenacityTransport)
    assert captured_kwargs.get("event_hooks") in (None, {})


@pytest.mark.parametrize(
    "delay_value,should_raise",
    [
        (0.0, False),  # Valid: minimum
        (30.0, False),  # Valid: middle
        (60.0, False),  # Valid: maximum
        (-1.0, True),  # Invalid: negative
        (61.0, True),  # Invalid: exceeds max
        (100.0, True),  # Invalid: way over
    ],
)
def test_request_delay_validation(
    state_manager: StateManager, delay_value: float, should_raise: bool
) -> None:
    """Validation should reject delays outside 0-60 second range."""
    state_manager.session.user_config["settings"]["request_delay"] = delay_value

    if should_raise:
        with pytest.raises(ValueError, match="request_delay must be between"):
            ac.get_or_create_agent("openai:gpt-4", state_manager)
    else:
        # Should not raise
        ac.get_or_create_agent("openai:gpt-4", state_manager)


def test_request_delay_change_invalidation(
    monkeypatch: pytest.MonkeyPatch, state_manager: StateManager
) -> None:
    """Changing request_delay should rebuild the agent to apply new hooks."""
    captured_event_hooks: list[dict] = []

    class RecordingAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            captured_event_hooks.append(kwargs.get("event_hooks") or {})
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(ac, "AsyncClient", RecordingAsyncClient)

    state_manager.session.user_config["settings"]["request_delay"] = 0.0
    ac.get_or_create_agent("openai:gpt-4.1", state_manager)

    state_manager.session.user_config["settings"]["request_delay"] = 1.0
    ac.get_or_create_agent("openai:gpt-4.1", state_manager)

    assert len(captured_event_hooks) == 2
    assert captured_event_hooks[0].get("request") in (None, [])

    updated_request_hooks = captured_event_hooks[1].get("request")
    assert updated_request_hooks, "Expected rebuilt agent to include request delay hook"


@pytest.mark.asyncio
async def test_request_delay_countdown_updates_streaming_panel(
    monkeypatch: pytest.MonkeyPatch, state_manager: StateManager
) -> None:
    """Countdown should surface via streaming panel when spinner is absent."""
    state_manager.session.user_config["settings"]["request_delay"] = 0.6
    captured_hooks: dict = {}

    class RecordingAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            captured_hooks.update(kwargs.get("event_hooks") or {})
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(ac, "AsyncClient", RecordingAsyncClient)

    class StubPanel:
        def __init__(self) -> None:
            self.status_messages: list[str] = []
            self.clears = 0

        async def set_status_message(self, message: str) -> None:
            self.status_messages.append(message)

        async def clear_status_message(self) -> None:
            self.clears += 1

    panel = StubPanel()
    state_manager.session.streaming_panel = panel
    state_manager.session.spinner = None

    sleep_calls: list[float] = []

    async def fake_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    monkeypatch.setattr(ac.asyncio, "sleep", fake_sleep)

    ac.get_or_create_agent("openai:gpt-4.1", state_manager)

    request_hooks = captured_hooks.get("request")
    assert request_hooks, "Expected request hooks for configured delay"
    hook = request_hooks[0]

    await hook(httpx.Request("GET", "http://example.com"))

    assert panel.status_messages, "Countdown should update streaming panel"
    assert panel.status_messages[0].startswith(ac.REQUEST_DELAY_MESSAGE_PREFIX)
    assert panel.clears == 1
    assert sum(sleep_calls) == pytest.approx(0.6)
