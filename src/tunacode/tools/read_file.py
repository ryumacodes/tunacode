"""File reading tool for agent operations."""

import asyncio
import os

from tunacode.exceptions import ToolExecutionError

from tunacode.tools.decorators import file_tool
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


def _truncate_line(line_text: str, line_limit: int) -> str:
    """Truncate a line if it exceeds the limit, appending an ellipsis."""
    if len(line_text) > line_limit:
        return line_text[:line_limit] + TRUNCATION_SUFFIX
    return line_text


@file_tool
async def read_file(
    filepath: str,
    offset: int = 0,
    limit: int | None = None,
) -> str:
    """Read the contents of a file with line limiting and truncation.

    Args:
        filepath: The absolute path to the file to read.
        offset: The line number to start reading from (0-based). Defaults to 0.
        limit: The number of lines to read. Defaults to DEFAULT_READ_LIMIT (2000).

    Returns:
        The formatted file contents with content-hash tagged line numbers.

    Notes:
        Each call replaces the cache for ``filepath`` with only the lines returned
        by that read (paginated reads do not merge prior cache windows).
        ``hashline_edit`` can only edit lines present in the current cache and
        raises ``ToolRetryError`` with an offset hint when a requested line is
        missing from cache.
    """
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        raise ToolExecutionError(
            tool_name="read_file",
            message=ERROR_FILE_TOO_LARGE.format(filepath=filepath) + MSG_FILE_SIZE_LIMIT,
        )

    effective_limit = limit if limit is not None else DEFAULT_READ_LIMIT
    max_line_len = MAX_LINE_LENGTH

    def _read_sync(
        path: str,
        line_limit: int,
        line_offset: int,
        line_count: int,
    ) -> tuple[str, list[HashedLine]]:
        display_lines: list[str] = []
        hashed_lines: list[HashedLine] = []
        skipped_lines = 0

        with open(path, encoding=DEFAULT_FILE_ENCODING) as f:
            for _ in range(line_offset):
                line = f.readline()
                if not line:
                    break
                skipped_lines += 1

            for line_index in range(line_count):
                line = f.readline()
                if not line:
                    break
                line_text = line.rstrip("\n")
                line_number = skipped_lines + line_index + 1

                # Build the HashedLine from the *original* content (pre-truncation)
                h = content_hash(line_text)
                hl = HashedLine(line_number=line_number, hash=h, content=line_text)
                hashed_lines.append(hl)

                # Display may be truncated but cache stores the full line
                truncated_text = _truncate_line(line_text, line_limit)
                display_hl = HashedLine(
                    line_number=line_number,
                    hash=h,
                    content=truncated_text,
                )
                display_lines.append(format_hashline(display_hl))

            extra_line = f.readline()
            has_more_lines = bool(extra_line)

        last_line = skipped_lines + len(display_lines)

        output = f"{FILE_TAG_OPEN}\n"
        output += "\n".join(display_lines)

        if has_more_lines:
            output += f"\n\n{MORE_LINES_MESSAGE.format(last_line=last_line)}"
            output += f"\n{FILE_TAG_CLOSE}"
            return output, hashed_lines

        total_lines = last_line
        output += f"\n\n{END_OF_FILE_MESSAGE.format(total_lines=total_lines)}"
        output += f"\n{FILE_TAG_CLOSE}"
        return output, hashed_lines

    result, hashed = await asyncio.to_thread(
        _read_sync,
        filepath,
        max_line_len,
        offset,
        effective_limit,
    )

    # Populate the line cache so hashline_edit can validate references
    _cache_store(filepath, hashed)

    return result
