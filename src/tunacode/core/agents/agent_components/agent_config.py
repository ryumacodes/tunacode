"""Agent configuration and creation utilities."""

from __future__ import annotations

# ruff: noqa: I001

import asyncio
import hashlib
import os
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import httpx
from tinyagent import Agent, AgentOptions
from tinyagent.agent_types import (
    AgentMessage,
    AgentTool,
    AgentToolResult,
    AgentToolUpdateCallback,
    Context,
    JsonObject,
    Model,
    SimpleStreamOptions,
    StreamFn,
    StreamResponse,
)
from tinyagent.alchemy_provider import OpenAICompatModel, stream_alchemy_openai_completions

from tunacode.configuration.limits import get_max_tokens
from tunacode.configuration.models import (
    get_provider_alchemy_api,
    get_provider_base_url,
    get_provider_env_var,
    load_models_registry,
    parse_model_string,
)
from tunacode.constants import AGENTS_MD, ENV_OPENAI_BASE_URL
from tunacode.prompts.versioning import (
    compute_agent_prompt_versions,
    get_or_compute_prompt_version,
)
from tunacode.skills.models import SelectedSkill
from tunacode.skills.prompting import (
    compute_skills_prompt_fingerprint,
    render_available_skills_block,
    render_selected_skills_block,
)
from tunacode.skills.registry import list_skill_summaries
from tunacode.skills.selection import resolve_selected_skills
from tunacode.types import ModelName
from tunacode.types.canonical import AgentPromptVersions, PromptVersion

from tunacode.tools.bash import bash
from tunacode.tools.decorators import to_tinyagent_tool
from tunacode.tools.discover import discover
from tunacode.tools.hashline_edit import hashline_edit
from tunacode.tools.read_file import read_file
from tunacode.tools.web_fetch import web_fetch
from tunacode.tools.write_file import write_file
from tunacode.tools.xml_helper import get_xml_prompt_path

from tunacode.infrastructure.cache.caches import agents as agents_cache
from tunacode.infrastructure.cache.caches import tunacode_context as context_cache

from tunacode.core.compaction.controller import get_or_create_compaction_controller
from tunacode.core.logging.manager import LogManager, get_logger
from tunacode.core.types.state import SessionStateProtocol, StateManagerProtocol

ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_CHAT_COMPLETIONS_PATH = "/chat/completions"
OPENROUTER_PROVIDER_ID = "openrouter"
MAX_PARALLEL_TOOL_CALLS = 3
MIN_PARALLEL_TOOL_CALLS = 1
MAX_STREAM_RETRY_DELAY_SECONDS = 8.0
STREAM_RETRYABLE_STATUS_CODES = frozenset({408, 409, 425, 429})

ToolExecute = Callable[
    [str, JsonObject, asyncio.Event | None, AgentToolUpdateCallback],
    Awaitable[AgentToolResult],
]


@dataclass(frozen=True, slots=True)
class AgentSettings:
    request_delay: float
    global_request_timeout: float | None
    max_retries: int
    tool_strict_validation: bool


@dataclass(frozen=True, slots=True)
class SessionConfig:
    settings: AgentSettings
    env: dict[str, str]


@dataclass(frozen=True, slots=True)
class SkillsPromptState:
    available_block: str
    selected_block: str
    fingerprint: str
    selected_skills: list[SelectedSkill]


async def _sleep_with_delay(total_delay: float) -> None:
    await asyncio.sleep(total_delay)


def _coerce_mapping(value: object, *, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{field_name} must be a dict, got {type(value).__name__}")
    if not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} keys must be strings")
    return {key: raw_value for key, raw_value in value.items() if isinstance(key, str)}


def _coerce_int_setting(settings: Mapping[str, object], key: str, default: int) -> int:
    value = settings.get(key, default)
    if isinstance(value, bool):
        raise TypeError(f"{key} must be an integer, got bool")
    if isinstance(value, int):
        return value
    if not isinstance(value, (str, float)):
        raise TypeError(f"{key} must be an integer-like value")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{key} must be an integer-like value") from exc


def _coerce_float_setting(settings: Mapping[str, object], key: str, default: float) -> float:
    value = settings.get(key, default)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a float-like value")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{key} must be a float-like value") from exc


def _coerce_bool_setting(settings: Mapping[str, object], key: str, default: bool) -> bool:
    value = settings.get(key, default)
    if isinstance(value, bool):
        return value
    raise TypeError(f"{key} must be a bool, got {type(value).__name__}")


def _normalize_session_config(session: SessionStateProtocol) -> SessionConfig:
    raw_user_config = _coerce_mapping(cast(object, session.user_config), field_name="user_config")
    raw_settings = _coerce_mapping(raw_user_config.get("settings", {}), field_name="settings")
    raw_env = _coerce_mapping(raw_user_config.get("env", {}), field_name="env")

    request_delay = _coerce_float_setting(raw_settings, "request_delay", 0.0)
    if request_delay < 0.0 or request_delay > 60.0:
        raise ValueError(f"request_delay must be between 0.0 and 60.0 seconds, got {request_delay}")

    timeout = _coerce_float_setting(raw_settings, "global_request_timeout", 600.0)
    if timeout < 0.0:
        raise ValueError(f"global_request_timeout must be >= 0.0 seconds, got {timeout}")

    env_config = {
        key: value.strip()
        for key, value in raw_env.items()
        if isinstance(value, str) and value.strip()
    }
    settings = AgentSettings(
        request_delay=request_delay,
        global_request_timeout=None if timeout == 0.0 else timeout,
        max_retries=_coerce_int_setting(raw_settings, "max_retries", 3),
        tool_strict_validation=_coerce_bool_setting(
            raw_settings,
            "tool_strict_validation",
            False,
        ),
    )
    if settings.max_retries < 1:
        raise ValueError(f"max_retries must be >= 1, got {settings.max_retries}")
    return SessionConfig(settings=settings, env=env_config)


def _coerce_session_config(config: SessionConfig | SessionStateProtocol) -> SessionConfig:
    if isinstance(config, SessionConfig):
        return config
    return _normalize_session_config(config)


def _coerce_request_delay(session: SessionStateProtocol) -> float:
    return _normalize_session_config(session).settings.request_delay


def _coerce_global_request_timeout(session: SessionStateProtocol) -> float | None:
    return _normalize_session_config(session).settings.global_request_timeout


def _compute_agent_version(
    settings: AgentSettings,
    *,
    max_tokens: int | None,
    skills_prompt_fingerprint: str,
) -> int:
    return hash(
        (
            settings.max_retries,
            settings.tool_strict_validation,
            settings.request_delay,
            settings.global_request_timeout,
            max_tokens,
            MAX_PARALLEL_TOOL_CALLS,
            skills_prompt_fingerprint,
        )
    )


def invalidate_agent_cache(model: str, state_manager: StateManagerProtocol) -> bool:
    """Invalidate cached agent for a specific model."""
    logger = get_logger()
    cleared_module = agents_cache.invalidate_agent(model)
    cleared_session = False

    session_agents = _session_agents_dict(state_manager.session)
    if model in session_agents:
        del session_agents[model]
        cleared_session = True
    state_manager.session.agent_versions.pop(model, None)

    invalidated = cleared_module or cleared_session
    if invalidated:
        logger.debug(
            f"Agent cache cleared: model={model}, "
            f"module={cleared_module}, session={cleared_session}"
        )
    return invalidated


def load_system_prompt(
    base_path: Path,
    model: str | None = None,
) -> tuple[str, PromptVersion | None]:
    _ = model
    prompt_file = base_path / "prompts" / "system_prompt.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Required prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8"), get_or_compute_prompt_version(prompt_file)


def load_tunacode_context() -> tuple[str, PromptVersion | None]:
    logger = get_logger()
    try:
        tunacode_path = Path.cwd() / AGENTS_MD
        return context_cache.get_context(tunacode_path), get_or_compute_prompt_version(
            tunacode_path
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Unexpected error loading guide file: {exc}")
        raise


def _wrap_tool_with_concurrency_limit(tool: AgentTool, *, limiter: asyncio.Semaphore) -> AgentTool:
    raw_execute_fn = cast(object, tool.execute)
    if raw_execute_fn is None:
        raise ValueError(f"Tool '{tool.name}' must define an execute handler")
    typed_execute_fn = cast(ToolExecute, raw_execute_fn)

    async def _execute_with_limit(
        tool_call_id: str,
        args: JsonObject,
        signal: asyncio.Event | None,
        on_update: AgentToolUpdateCallback,
    ) -> AgentToolResult:
        await limiter.acquire()
        try:
            return await typed_execute_fn(tool_call_id, args, signal, on_update)
        finally:
            limiter.release()

    tool.execute = _execute_with_limit
    return tool


def _apply_tool_concurrency_limit(
    tools: Sequence[AgentTool],
    *,
    max_parallel_tool_calls: int = MAX_PARALLEL_TOOL_CALLS,
) -> list[AgentTool]:
    if max_parallel_tool_calls < MIN_PARALLEL_TOOL_CALLS:
        raise ValueError(
            f"max_parallel_tool_calls must be >= {MIN_PARALLEL_TOOL_CALLS}, "
            f"got {max_parallel_tool_calls}"
        )
    limiter = asyncio.Semaphore(max_parallel_tool_calls)
    return [_wrap_tool_with_concurrency_limit(tool, limiter=limiter) for tool in tools]


def _build_tools(*, strict_validation: bool = False) -> list[AgentTool]:
    tool_functions: tuple[object, ...] = (
        cast(object, bash),
        cast(object, discover),
        cast(object, read_file),
        cast(object, hashline_edit),
        cast(object, web_fetch),
        cast(object, write_file),
    )
    tools = [
        _to_agent_tool(tool_fn, strict_validation=strict_validation) for tool_fn in tool_functions
    ]
    return _apply_tool_concurrency_limit(tools)


def _to_agent_tool(tool_fn: object, *, strict_validation: bool = False) -> AgentTool:
    return to_tinyagent_tool(tool_fn, strict_validation=strict_validation)  # type: ignore[arg-type]


def _normalize_chat_completions_url(base_url: str | None) -> str | None:
    if not isinstance(base_url, str):
        return None
    stripped = base_url.strip()
    if not stripped:
        return None
    if stripped.endswith(OPENAI_CHAT_COMPLETIONS_PATH):
        return stripped
    return f"{stripped.rstrip('/')}{OPENAI_CHAT_COMPLETIONS_PATH}"


def _resolve_base_url(config: SessionConfig | SessionStateProtocol, provider_id: str) -> str | None:
    session_config = _coerce_session_config(config)
    configured_base_url = _normalize_chat_completions_url(
        session_config.env.get(ENV_OPENAI_BASE_URL)
    )
    if configured_base_url is not None:
        return configured_base_url
    load_models_registry()
    return _normalize_chat_completions_url(get_provider_base_url(provider_id))


def _require_provider_base_url(provider_id: str, base_url: str | None) -> str | None:
    if base_url is not None or provider_id == OPENROUTER_PROVIDER_ID:
        return base_url
    raise ValueError(
        "Provider has no configured API base URL. "
        f"Set {ENV_OPENAI_BASE_URL} or add provider.api to models_registry for '{provider_id}'."
    )


def _build_api_key_resolver(
    env_config: Mapping[str, str] | SessionStateProtocol,
) -> Callable[[str], str | None]:
    if isinstance(env_config, Mapping):

        def env_getter() -> Mapping[str, str]:
            return env_config
    else:
        session = env_config

        def env_getter() -> Mapping[str, str]:
            raw_user_config = _coerce_mapping(
                cast(object, session.user_config),
                field_name="user_config",
            )
            raw_env = _coerce_mapping(raw_user_config.get("env", {}), field_name="env")
            return {
                key: value.strip()
                for key, value in raw_env.items()
                if isinstance(value, str) and value.strip()
            }

    def _read_api_key(env_var: str) -> str | None:
        configured = env_getter().get(env_var)
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        os_value = os.environ.get(env_var, "")
        return os_value.strip() or None

    def _resolve(provider_id: str) -> str | None:
        provider_env_var = get_provider_env_var(provider_id)
        provider_api_key = _read_api_key(provider_env_var)
        if provider_api_key is not None:
            return provider_api_key
        if provider_env_var == ENV_OPENAI_API_KEY:
            return None
        return _read_api_key(ENV_OPENAI_API_KEY)

    return _resolve


def _merge_stream_options(
    *,
    options: SimpleStreamOptions,
    max_tokens: int | None,
) -> SimpleStreamOptions:
    if max_tokens is None:
        return options
    update_values: dict[str, object] = {"max_tokens": max_tokens}
    return options.model_copy(update=update_values)


def _is_retryable_stream_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        response = exc.response
        if response is None:
            return False
        return response.status_code in STREAM_RETRYABLE_STATUS_CODES or response.status_code >= 500
    return isinstance(exc, (httpx.RequestError, TimeoutError))


def _compute_stream_retry_delay(attempt_number: int) -> float:
    return min(0.5 * (2 ** (attempt_number - 1)), MAX_STREAM_RETRY_DELAY_SECONDS)


def _build_stream_fn(
    *,
    request_delay: float,
    max_tokens: int | None,
    max_retries: int = 1,
) -> StreamFn:
    async def _stream(
        model: Model,
        context: Context,
        options: SimpleStreamOptions,
    ) -> StreamResponse:
        stream_options = _merge_stream_options(options=options, max_tokens=max_tokens)

        for attempt in range(1, max_retries + 1):
            if request_delay > 0:
                await _sleep_with_delay(request_delay)
            try:
                return await stream_alchemy_openai_completions(model, context, stream_options)
            except Exception as exc:  # noqa: BLE001
                if attempt >= max_retries or not _is_retryable_stream_error(exc):
                    raise
                get_logger().warning(
                    "Retrying provider stream request after transient error: "
                    f"attempt={attempt}/{max_retries}, error={type(exc).__name__}"
                )
                await _sleep_with_delay(_compute_stream_retry_delay(attempt))

        raise RuntimeError("Unreachable stream retry exhaustion")

    return _stream


def _build_transform_context(
    state_manager: StateManagerProtocol,
) -> Callable[[list[AgentMessage], asyncio.Event | None], Awaitable[list[AgentMessage]]]:
    async def _transform_context(
        messages: list[AgentMessage],
        signal: asyncio.Event | None,
    ) -> list[AgentMessage]:
        controller = get_or_create_compaction_controller(state_manager)
        session = state_manager.session
        compaction_outcome = await controller.check_and_compact(
            messages,
            max_tokens=session.conversation.max_tokens,
            signal=signal,
            allow_threshold=False,
        )
        return controller.inject_summary_message(compaction_outcome.messages)

    return _transform_context


def _build_tinyagent_model(
    model: ModelName,
    config: SessionConfig | SessionStateProtocol,
) -> OpenAICompatModel:
    session_config = _coerce_session_config(config)
    provider_id, model_id = parse_model_string(model)
    base_url = _require_provider_base_url(
        provider_id,
        _resolve_base_url(session_config, provider_id),
    )
    alchemy_api = get_provider_alchemy_api(provider_id)
    if base_url is not None and alchemy_api is not None:
        return OpenAICompatModel(
            provider=provider_id,
            id=model_id,
            api=alchemy_api,
            base_url=base_url,
        )
    if base_url is not None:
        return OpenAICompatModel(provider=provider_id, id=model_id, base_url=base_url)
    if alchemy_api is not None:
        return OpenAICompatModel(provider=provider_id, id=model_id, api=alchemy_api)
    return OpenAICompatModel(provider=provider_id, id=model_id)


def _build_skills_prompt_state(session: SessionStateProtocol) -> SkillsPromptState:
    available_skill_summaries = list_skill_summaries()
    selected_skills = resolve_selected_skills(session.selected_skill_names)
    return SkillsPromptState(
        available_block=render_available_skills_block(available_skill_summaries),
        selected_block=render_selected_skills_block(selected_skills),
        fingerprint=compute_skills_prompt_fingerprint(available_skill_summaries, selected_skills),
        selected_skills=selected_skills,
    )


def _augment_prompt_versions_with_skills(
    prompt_versions: AgentPromptVersions,
    *,
    skills_prompt_fingerprint: str,
) -> AgentPromptVersions:
    combined_fingerprint = hashlib.sha256(
        f"{prompt_versions.fingerprint}|skills:{skills_prompt_fingerprint}".encode()
    ).hexdigest()
    return AgentPromptVersions(
        system_prompt=prompt_versions.system_prompt,
        tunacode_context=prompt_versions.tunacode_context,
        tool_prompts=prompt_versions.tool_prompts,
        fingerprint=combined_fingerprint,
        computed_at=time.time(),
    )


def _get_session_cached_agent(session: SessionStateProtocol, model: ModelName) -> Agent | None:
    cached_agent = _session_agents_dict(session).get(model)
    if isinstance(cached_agent, Agent):
        return cached_agent
    if cached_agent is None:
        return None
    raise TypeError(f"session.agents[{model!r}] must be Agent, got {type(cached_agent).__name__}")


def _session_agents_dict(session: SessionStateProtocol) -> dict[str, object]:
    agents = cast(object, session.agents)
    if not isinstance(agents, dict):
        raise TypeError(f"session.agents must be a dict, got {type(agents).__name__}")
    if not all(isinstance(key, str) for key in agents):
        raise TypeError("session.agents keys must be strings")
    return cast(dict[str, object], agents)


def _collect_tool_prompt_paths(tools: Sequence[AgentTool]) -> dict[str, Path | str]:
    tool_prompt_paths: dict[str, Path | str] = {}
    for tool in tools:
        xml_path = get_xml_prompt_path(tool.name)
        if xml_path is not None:
            tool_prompt_paths[tool.name] = xml_path
    return tool_prompt_paths


def _build_agent_options(
    *,
    session: SessionStateProtocol,
    state_manager: StateManagerProtocol,
    config: SessionConfig,
    max_tokens: int | None,
) -> AgentOptions:
    return AgentOptions(
        stream_fn=_build_stream_fn(
            request_delay=config.settings.request_delay,
            max_tokens=max_tokens,
            max_retries=config.settings.max_retries,
        ),
        session_id=session.session_id,
        get_api_key=_build_api_key_resolver(config.env),
        transform_context=_build_transform_context(state_manager),
    )


def _log_agent_created(
    logger: LogManager,
    *,
    model: ModelName,
    system_version: PromptVersion | None,
    context_version: PromptVersion | None,
    prompt_versions: AgentPromptVersions,
) -> None:
    logger.info(
        f"Agent created: {model}, "
        f"system_prompt={system_version.content_hash[:12] if system_version else 'N/A'}, "
        f"context={context_version.content_hash[:12] if context_version else 'N/A'}, "
        f"fingerprint={prompt_versions.fingerprint[:12]}"
    )


def get_or_create_agent(model: ModelName, state_manager: StateManagerProtocol) -> Agent:
    """Get existing agent or create a new tinyagent Agent for the specified model."""
    logger = get_logger()
    session = state_manager.session
    session_agents = _session_agents_dict(session)
    config = _normalize_session_config(session)

    load_models_registry()
    skills_state = _build_skills_prompt_state(session)
    max_tokens = get_max_tokens()
    agent_version = _compute_agent_version(
        config.settings,
        max_tokens=max_tokens,
        skills_prompt_fingerprint=skills_state.fingerprint,
    )

    session_agent = _get_session_cached_agent(session, model)
    session_version = session.agent_versions.get(model)
    if session_agent is not None and session_version == agent_version:
        logger.debug(f"Agent cache hit (session): {model}")
        return session_agent
    if session_agent is not None and session_version != agent_version:
        logger.debug(f"Agent cache invalidated (session version mismatch): {model}")
        del session_agents[model]
        session.agent_versions.pop(model, None)

    base_path = Path(__file__).parent.parent.parent.parent
    system_prompt_content, system_version = load_system_prompt(base_path, model=model)
    tunacode_context_content, context_version = load_tunacode_context()
    system_prompt = (
        system_prompt_content
        + tunacode_context_content
        + skills_state.selected_block
        + skills_state.available_block
    )

    tools = _build_tools(strict_validation=config.settings.tool_strict_validation)
    prompt_versions = compute_agent_prompt_versions(
        system_prompt_path=base_path / "prompts" / "system_prompt.md",
        tunacode_context_path=Path.cwd() / AGENTS_MD,
        tool_prompt_paths=_collect_tool_prompt_paths(tools),
    )
    prompt_versions = _augment_prompt_versions_with_skills(
        prompt_versions,
        skills_prompt_fingerprint=skills_state.fingerprint,
    )

    agent = Agent(
        _build_agent_options(
            session=session,
            state_manager=state_manager,
            config=config,
            max_tokens=max_tokens,
        )
    )
    agent.set_system_prompt(system_prompt)
    agent.set_model(_build_tinyagent_model(model, config))
    agent.set_tools(tools)
    agent.prompt_versions = prompt_versions  # type: ignore[attr-defined]

    session.agent_versions[model] = agent_version
    session_agents[model] = agent

    _log_agent_created(
        logger,
        model=model,
        system_version=system_version,
        context_version=context_version,
        prompt_versions=prompt_versions,
    )
    return agent
