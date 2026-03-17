"""Shared session/config helpers for agent construction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from tunacode.core.types.state import SessionStateProtocol

from tunacode.skills.models import SelectedSkill


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
            3,
            skills_prompt_fingerprint,
        )
    )
