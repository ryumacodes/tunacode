"""HTTP response validation for OpenAI chat completions."""

from __future__ import annotations

import json
from typing import Any

from httpx import Response

from tunacode.exceptions import AgentError

from tunacode.core.logging import get_logger

CHAT_COMPLETIONS_PATH_FRAGMENT: str = "/chat/completions"
CONTENT_TYPE_HEADER: str = "content-type"
CONTENT_TYPE_EVENT_STREAM: str = "text/event-stream"

ERROR_FIELD: str = "error"
ERROR_MESSAGE_FIELD: str = "message"
ERROR_TYPE_FIELD: str = "type"
ERROR_CODE_FIELD: str = "code"
ERROR_PARAM_FIELD: str = "param"

FIELD_ID: str = "id"
FIELD_CHOICES: str = "choices"
FIELD_MODEL: str = "model"
FIELD_OBJECT: str = "object"
CHAT_COMPLETION_OBJECT: str = "chat.completion"

NON_DICT_PAYLOAD_FIELD: str = "_payload"

DETAIL_SEPARATOR: str = ", "
MISSING_FIELDS_SEPARATOR: str = ", "

DEFAULT_ERROR_MESSAGE: str = "OpenAI returned an error payload"
UNKNOWN_MODEL_NAME: str = "unknown-model"
UNKNOWN_PROVIDER_NAME: str = "unknown-provider"

ERROR_MESSAGE_TEMPLATE: str = (
    "OpenAI-compatible provider error from {provider} (model={model_name}): {error_message}"
)
INVALID_RESPONSE_TEMPLATE: str = (
    "Invalid OpenAI chat completion response from {provider} "
    "(model={model_name}, missing fields: {missing_fields})"
)

SUGGESTED_FIX_ERROR_PAYLOAD: str = "Check provider status and API key, then retry."
SUGGESTED_FIX_INVALID_RESPONSE: str = (
    "Verify the provider is OpenAI-compatible and the model name is correct."
)

DEFAULT_TROUBLESHOOTING_STEPS: list[str] = [
    "Confirm the provider base URL and API key are correct.",
    "Retry with a different model or provider.",
]

LOG_ERROR_PAYLOAD_MESSAGE: str = "OpenAI-compatible provider returned error payload"
LOG_INVALID_RESPONSE_MESSAGE: str = "OpenAI-compatible provider returned invalid payload"


def _is_chat_completion_request(response: Response) -> bool:
    request = response.request
    if request is None:
        return False

    request_path = request.url.path
    return CHAT_COMPLETIONS_PATH_FRAGMENT in request_path


def _is_streaming_response(response: Response) -> bool:
    content_type = response.headers.get(CONTENT_TYPE_HEADER, "")
    normalized_content_type = content_type.lower()
    return CONTENT_TYPE_EVENT_STREAM in normalized_content_type


async def _read_response_payload(response: Response) -> Any | None:
    await response.aread()
    payload_bytes = response.content
    if not payload_bytes:
        return None

    try:
        return json.loads(payload_bytes)
    except json.JSONDecodeError:
        return None


def _normalize_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload

    return {NON_DICT_PAYLOAD_FIELD: payload}


def _extract_error_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    error_payload = payload.get(ERROR_FIELD)
    if error_payload is None:
        return None

    if isinstance(error_payload, dict):
        return error_payload

    return {ERROR_MESSAGE_FIELD: str(error_payload)}


def _format_error_details(error_payload: dict[str, Any]) -> str | None:
    details: list[str] = []

    error_type = error_payload.get(ERROR_TYPE_FIELD)
    if error_type is not None:
        details.append(f"{ERROR_TYPE_FIELD}={error_type}")

    error_code = error_payload.get(ERROR_CODE_FIELD)
    if error_code is not None:
        details.append(f"{ERROR_CODE_FIELD}={error_code}")

    error_param = error_payload.get(ERROR_PARAM_FIELD)
    if error_param is not None:
        details.append(f"{ERROR_PARAM_FIELD}={error_param}")

    if not details:
        return None

    return DETAIL_SEPARATOR.join(details)


def _format_error_message(error_payload: dict[str, Any]) -> str:
    raw_message = error_payload.get(ERROR_MESSAGE_FIELD)
    message = str(raw_message) if raw_message else DEFAULT_ERROR_MESSAGE

    details = _format_error_details(error_payload)
    if details:
        return f"{message} ({details})"

    return message


def _collect_missing_fields(payload: dict[str, Any]) -> list[str]:
    missing_fields: list[str] = []

    response_id = payload.get(FIELD_ID)
    if response_id is None:
        missing_fields.append(FIELD_ID)

    response_choices = payload.get(FIELD_CHOICES)
    if not isinstance(response_choices, list) or not response_choices:
        missing_fields.append(FIELD_CHOICES)

    response_model = payload.get(FIELD_MODEL)
    if not isinstance(response_model, str) or not response_model:
        missing_fields.append(FIELD_MODEL)

    response_object = payload.get(FIELD_OBJECT)
    if response_object != CHAT_COMPLETION_OBJECT:
        missing_fields.append(FIELD_OBJECT)

    return missing_fields


def _extract_provider_name(response: Response) -> str:
    request = response.request
    if request is None:
        return UNKNOWN_PROVIDER_NAME

    provider_name = request.url.host
    if provider_name:
        return provider_name

    return str(request.url)


def _extract_model_name(response: Response) -> str:
    request = response.request
    if request is None:
        return UNKNOWN_MODEL_NAME

    request_payload = _load_request_payload(request.content)
    if not isinstance(request_payload, dict):
        return UNKNOWN_MODEL_NAME

    model_name = request_payload.get(FIELD_MODEL)
    if isinstance(model_name, str) and model_name.strip():
        return model_name

    return UNKNOWN_MODEL_NAME


def _load_request_payload(request_body: Any) -> Any | None:
    if request_body is None:
        return None

    if isinstance(request_body, bytes):
        raw_body = request_body
    elif isinstance(request_body, str):
        raw_body = request_body.encode()
    else:
        raw_body = str(request_body).encode()

    if not raw_body:
        return None

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        return None


async def validate_openai_chat_completion_response(response: Response) -> None:
    if not _is_chat_completion_request(response):
        return

    if _is_streaming_response(response):
        return

    payload = await _read_response_payload(response)
    if payload is None:
        return

    normalized_payload = _normalize_payload(payload)
    error_payload = _extract_error_payload(normalized_payload)
    provider_name = _extract_provider_name(response)
    model_name = _extract_model_name(response)

    logger = get_logger()

    if error_payload is not None:
        error_message = _format_error_message(error_payload)
        logger.error(
            LOG_ERROR_PAYLOAD_MESSAGE,
            extra={
                "provider": provider_name,
                "model": model_name,
                "error": error_payload,
            },
        )
        raise AgentError(
            ERROR_MESSAGE_TEMPLATE.format(
                provider=provider_name,
                model_name=model_name,
                error_message=error_message,
            ),
            suggested_fix=SUGGESTED_FIX_ERROR_PAYLOAD,
            troubleshooting_steps=DEFAULT_TROUBLESHOOTING_STEPS,
        )

    missing_fields = _collect_missing_fields(normalized_payload)
    if not missing_fields:
        return

    missing_fields_summary = MISSING_FIELDS_SEPARATOR.join(missing_fields)
    logger.error(
        LOG_INVALID_RESPONSE_MESSAGE,
        extra={
            "provider": provider_name,
            "model": model_name,
            "missing_fields": missing_fields,
        },
    )
    raise AgentError(
        INVALID_RESPONSE_TEMPLATE.format(
            provider=provider_name,
            model_name=model_name,
            missing_fields=missing_fields_summary,
        ),
        suggested_fix=SUGGESTED_FIX_INVALID_RESPONSE,
        troubleshooting_steps=DEFAULT_TROUBLESHOOTING_STEPS,
    )
