"""Native tinyagent read_file tool."""

from __future__ import annotations

import asyncio
import os

from tinyagent.agent_types import (
    AgentTool,
    AgentToolResult,
    AgentToolUpdateCallback,
    JsonObject,
    TextContent,
)

from tunacode.exceptions import (
    FileOperationError,
    ToolExecutionError,
    ToolRetryError,
    UserAbortError,
)

from tunacode.tools.hashline import HashedLine, content_hash, format_hashline
from tunacode.tools.line_cache import store as _cache_store

KB_BYTES = 1024
MAX_FILE_SIZE_KB = 100
MAX_FILE_SIZE = MAX_FILE_SIZE_KB * KB_BYTES
ERROR_FILE_TOO_LARGE = f"Error: File '{{filepath}}' is too large (> {MAX_FILE_SIZE_KB}KB)."
MSG_FILE_SIZE_LIMIT = " Please specify a smaller file or use other tools to process it."
DEFAULT_READ_LIMIT = 2000
MAX_LINE_LENGTH = 2000
DEFAULT_FILE_ENCODING = "utf-8"
TRUNCATION_SUFFIX = "..."
FILE_TAG_OPEN = "<file>"
FILE_TAG_CLOSE = "</file>"
MORE_LINES_MESSAGE = "(File has more lines. Use 'offset' to read beyond line {last_line})"
END_OF_FILE_MESSAGE = "(End of file - total {total_lines} lines)"

_READ_FILE_DESCRIPTION = """Read the contents of a file with line limiting and truncation.

Each call replaces the cache for filepath with only the lines returned by that read.
hashline_edit can only edit lines present in the current cache and raises ToolRetryError
with an offset hint when a requested line is missing from cache.
"""

_READ_FILE_PARAMETERS: JsonObject = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "filepath": {"type": "string", "description": "Absolute path to the file to read."},
        "offset": {"type": "integer", "description": "0-based line offset to start from."},
        "limit": {"type": "integer", "description": "Maximum number of lines to read."},
    },
    "required": ["filepath"],
}


def _text_result(text: str) -> AgentToolResult:
    return AgentToolResult(content=[TextContent(text=text)], details={})


def _truncate_line(line_text: str, line_limit: int) -> str:
    if len(line_text) > line_limit:
        return line_text[:line_limit] + TRUNCATION_SUFFIX
    return line_text


async def _run_read_file(filepath: str, offset: int = 0, limit: int | None = None) -> str:
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        raise ToolExecutionError(
            tool_name="read_file",
            message=ERROR_FILE_TOO_LARGE.format(filepath=filepath) + MSG_FILE_SIZE_LIMIT,
        )

    effective_limit = limit if limit is not None else DEFAULT_READ_LIMIT

    def _read_sync(
        path: str,
        line_limit: int,
        line_offset: int,
        line_count: int,
    ) -> tuple[str, list[HashedLine]]:
        display_lines: list[str] = []
        hashed_lines: list[HashedLine] = []
        skipped_lines = 0

        with open(path, encoding=DEFAULT_FILE_ENCODING) as file_obj:
            for _ in range(line_offset):
                line = file_obj.readline()
                if not line:
                    break
                skipped_lines += 1

            for line_index in range(line_count):
                line = file_obj.readline()
                if not line:
                    break
                line_text = line.rstrip("\n")
                line_number = skipped_lines + line_index + 1

                line_hash = content_hash(line_text)
                hashed_line = HashedLine(line_number=line_number, hash=line_hash, content=line_text)
                hashed_lines.append(hashed_line)

                display_line = HashedLine(
                    line_number=line_number,
                    hash=line_hash,
                    content=_truncate_line(line_text, line_limit),
                )
                display_lines.append(format_hashline(display_line))

            extra_line = file_obj.readline()
            has_more_lines = bool(extra_line)

        last_line = skipped_lines + len(display_lines)
        output = f"{FILE_TAG_OPEN}\n" + "\n".join(display_lines)
        if has_more_lines:
            output += f"\n\n{MORE_LINES_MESSAGE.format(last_line=last_line)}"
            output += f"\n{FILE_TAG_CLOSE}"
            return output, hashed_lines

        output += f"\n\n{END_OF_FILE_MESSAGE.format(total_lines=last_line)}"
        output += f"\n{FILE_TAG_CLOSE}"
        return output, hashed_lines

    result, hashed = await asyncio.to_thread(
        _read_sync,
        filepath,
        MAX_LINE_LENGTH,
        offset,
        effective_limit,
    )
    _cache_store(filepath, hashed)
    return result


async def _execute_read_file(  # noqa: C901
    tool_call_id: str,
    args: JsonObject,
    signal: asyncio.Event | None,
    on_update: AgentToolUpdateCallback,
) -> AgentToolResult:
    _ = (tool_call_id, on_update)
    if signal is not None and signal.is_set():
        raise UserAbortError("Tool execution aborted: read_file")

    filepath = args.get("filepath")
    offset = args.get("offset", 0)
    limit = args.get("limit")
    if not isinstance(filepath, str):
        raise ToolRetryError("Invalid arguments for tool 'read_file': 'filepath' must be a string.")
    if not isinstance(offset, int) or isinstance(offset, bool):
        raise ToolRetryError("Invalid arguments for tool 'read_file': 'offset' must be an integer.")
    if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool)):
        raise ToolRetryError("Invalid arguments for tool 'read_file': 'limit' must be an integer.")

    try:
        result = await _run_read_file(filepath=filepath, offset=offset, limit=limit)
    except FileNotFoundError as err:
        raise ToolRetryError(f"File not found: {filepath}. Check the path.") from err
    except PermissionError as exc:
        raise FileOperationError(
            operation="access",
            path=filepath,
            message=str(exc),
            original_error=exc,
        ) from exc
    except UnicodeDecodeError as exc:
        raise FileOperationError(
            operation="decode",
            path=filepath,
            message=str(exc),
            original_error=exc,
        ) from exc
    except OSError as exc:
        raise FileOperationError(
            operation="read/write",
            path=filepath,
            message=str(exc),
            original_error=exc,
        ) from exc
    except (ToolRetryError, ToolExecutionError, FileOperationError):
        raise
    except Exception as exc:  # noqa: BLE001
        raise ToolExecutionError(
            tool_name="read_file",
            message=str(exc),
            original_error=exc,
        ) from exc

    return _text_result(result)


read_file = AgentTool(
    name="read_file",
    label="read_file",
    description=_READ_FILE_DESCRIPTION,
    parameters=_READ_FILE_PARAMETERS,
    execute=_execute_read_file,
)
