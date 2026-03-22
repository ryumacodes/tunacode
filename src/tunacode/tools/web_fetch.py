"""Native tinyagent web_fetch tool."""

from __future__ import annotations

import asyncio
import ipaddress
import re
from typing import NoReturn
from urllib.parse import urlparse

import html2text
import httpx
from tinyagent.agent_types import (
    AgentTool,
    AgentToolResult,
    AgentToolUpdateCallback,
    JsonObject,
    TextContent,
)

from tunacode.exceptions import ToolExecutionError, ToolRetryError, UserAbortError

MAX_CONTENT_SIZE = 5 * 1024 * 1024
MAX_OUTPUT_SIZE = 100 * 1024
DEFAULT_TIMEOUT = 60
USER_AGENT = "TunaCode/1.0 (https://tunacode.xyz)"

PRIVATE_IP_PATTERNS = [
    re.compile(r"^127\."),
    re.compile(r"^10\."),
    re.compile(r"^172\.(1[6-9]|2[0-9]|3[01])\."),
    re.compile(r"^192\.168\."),
    re.compile(r"^0\."),
    re.compile(r"^169\.254\."),
    re.compile(r"^::1$"),
    re.compile(r"^fe80:"),
    re.compile(r"^fc00:"),
    re.compile(r"^fd00:"),
]

BLOCKED_HOSTNAMES = frozenset(
    ["localhost", "localhost.localdomain", "local", "0.0.0.0", "127.0.0.1", "::1"]
)

_WEB_FETCH_DESCRIPTION = """Fetch web content from a URL and return it as readable text."""

_WEB_FETCH_PARAMETERS: JsonObject = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "url": {"type": "string", "description": "HTTP or HTTPS URL to fetch."},
        "timeout": {"type": "integer", "description": "Request timeout in seconds."},
    },
    "required": ["url"],
}


def _text_result(text: str) -> AgentToolResult:
    return AgentToolResult(content=[TextContent(text=text)], details={})


def _is_private_ip(ip_str: str) -> bool:
    for pattern in PRIVATE_IP_PATTERNS:
        if pattern.match(ip_str):
            return True

    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except ValueError:
        return False


def _validate_url(url: str) -> str:
    if not url or not url.strip():
        raise ToolRetryError("URL cannot be empty.")

    stripped_url = url.strip()
    try:
        parsed = urlparse(stripped_url)
    except Exception as err:
        raise ToolRetryError(f"Invalid URL format: {url}") from err

    if parsed.scheme not in ("http", "https"):
        raise ToolRetryError(
            f"Invalid URL scheme '{parsed.scheme}'. Only http:// and https:// are allowed."
        )
    if not parsed.hostname:
        raise ToolRetryError(f"URL missing hostname: {url}")

    hostname = parsed.hostname.lower()
    if hostname in BLOCKED_HOSTNAMES:
        raise ToolRetryError(f"Blocked URL: {url}. Cannot fetch from localhost or local addresses.")
    if _is_private_ip(hostname):
        raise ToolRetryError(
            f"Blocked URL: {url}. Cannot fetch from private or reserved IP addresses."
        )

    return stripped_url


def _convert_html_to_text(html_content: str) -> str:
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.ignore_emphasis = False
    converter.body_width = 80
    converter.unicode_snob = True
    converter.skip_internal_links = True
    return converter.handle(html_content)


def _truncate_output(content: str, max_size: int = MAX_OUTPUT_SIZE) -> str:
    if len(content.encode("utf-8")) <= max_size:
        return content
    truncated = content[: max_size // 2]
    return truncated + "\n\n... [Content truncated due to size] ..."


def _raise_content_too_large(size: int) -> None:
    raise ToolRetryError(
        f"Content too large ({size // 1024 // 1024}MB). "
        f"Maximum allowed is {MAX_CONTENT_SIZE // 1024 // 1024}MB."
    )


async def _head_check_size(client: httpx.AsyncClient, validated_url: str) -> None:
    try:
        head_response = await client.head(validated_url)
        content_length = head_response.headers.get("content-length")
        if content_length and int(content_length) > MAX_CONTENT_SIZE:
            _raise_content_too_large(int(content_length))
    except httpx.HTTPError:
        pass


def _decode_response(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="replace")


def _maybe_convert_html(text_content: str, content_type: str) -> str:
    if "text/html" in content_type or "<html" in text_content[:1000].lower():
        return _convert_html_to_text(text_content)
    return text_content


async def _fetch_and_process(client: httpx.AsyncClient, validated_url: str) -> str:
    await _head_check_size(client, validated_url)

    response = await client.get(validated_url)
    response.raise_for_status()

    final_url = str(response.url)
    if final_url != validated_url:
        _validate_url(final_url)

    content = response.content
    if len(content) > MAX_CONTENT_SIZE:
        _raise_content_too_large(len(content))

    text_content = _decode_response(content)
    content_type = response.headers.get("content-type", "").lower()
    return _truncate_output(_maybe_convert_html(text_content, content_type))


_HTTP_STATUS_MESSAGES: dict[int, str] = {
    404: "Page not found (404): {url}. Check the URL.",
    403: "Access forbidden (403): {url}. The page may require authentication.",
    429: "Rate limited (429): {url}. Try again later.",
}


def _handle_http_error(url: str, err: httpx.HTTPStatusError) -> NoReturn:
    status = err.response.status_code
    template = _HTTP_STATUS_MESSAGES.get(status)
    if template:
        raise ToolRetryError(template.format(url=url)) from err
    if status >= 500:
        raise ToolRetryError(f"Server error ({status}): {url}. The server may be down.") from err
    raise ToolRetryError(f"HTTP error {status} fetching {url}") from err


async def _run_web_fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    validated_url = _validate_url(url)
    bounded_timeout = max(5, min(timeout, 120))
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(bounded_timeout),
            follow_redirects=True,
            max_redirects=5,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            return await _fetch_and_process(client, validated_url)
    except httpx.TimeoutException as err:
        raise ToolRetryError(
            "Request timed out after "
            f"{bounded_timeout} seconds. Try again or use a shorter timeout."
        ) from err
    except httpx.TooManyRedirects as err:
        raise ToolRetryError(
            f"Too many redirects while fetching {url}. The URL may be invalid."
        ) from err
    except httpx.HTTPStatusError as err:
        _handle_http_error(url, err)
    except httpx.RequestError as err:
        raise ToolRetryError(f"Failed to connect to {url}: {err}") from err


async def _execute_web_fetch(
    tool_call_id: str,
    args: JsonObject,
    signal: asyncio.Event | None,
    on_update: AgentToolUpdateCallback,
) -> AgentToolResult:
    _ = (tool_call_id, on_update)
    if signal is not None and signal.is_set():
        raise UserAbortError("Tool execution aborted: web_fetch")

    url = args.get("url")
    timeout = args.get("timeout", DEFAULT_TIMEOUT)
    if not isinstance(url, str):
        raise ToolRetryError("Invalid arguments for tool 'web_fetch': 'url' must be a string.")
    if not isinstance(timeout, int) or isinstance(timeout, bool):
        raise ToolRetryError(
            "Invalid arguments for tool 'web_fetch': 'timeout' must be an integer."
        )

    try:
        result = await _run_web_fetch(url=url, timeout=timeout)
    except (ToolRetryError, ToolExecutionError):
        raise
    except Exception as exc:  # noqa: BLE001
        raise ToolExecutionError(
            tool_name="web_fetch",
            message=str(exc),
            original_error=exc,
        ) from exc

    return _text_result(result)


web_fetch = AgentTool(
    name="web_fetch",
    label="web_fetch",
    description=_WEB_FETCH_DESCRIPTION,
    parameters=_WEB_FETCH_PARAMETERS,
    execute=_execute_web_fetch,
)
