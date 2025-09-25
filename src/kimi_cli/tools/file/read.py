import re
from pathlib import Path
from typing import override

import aiofiles
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from kimi_cli.agent import BuiltinSystemPromptArgs

_MAX_LINES = 2000
_MAX_LINE_LENGTH = 2000


def _truncate_line(line: str, max_length: int = _MAX_LINE_LENGTH) -> str:
    """Truncate a line if it exceeds max_length, preserving the beginning."""
    if len(line) <= max_length:
        return line
    m = re.match(r"[\r\n]+$", line)
    linebreak = m.group(0) if m else ""
    end = "..." + linebreak
    return line[: max_length - len(end)] + end


class Params(BaseModel):
    path: str = Field(description="The absolute path to the file to read")
    line_offset: int = Field(
        description=(
            "The line number to start reading from. "
            "By default read from the beginning of the file. "
            "Set this when the file is too large to read at once."
        ),
        default=1,
    )
    n_lines: int = Field(
        description=(
            "The number of lines to read. "
            f"By default read up to {_MAX_LINES} lines, which is the max allowed value. "
            "Set this value when the file is too large to read at once."
        ),
        default=_MAX_LINES,
    )


class ReadFile(CallableTool2[Params]):
    name: str = "ReadFile"
    description: str = (Path(__file__).parent / "read.md").read_text()
    params: type[Params] = Params

    def __init__(self, builtin_args: BuiltinSystemPromptArgs, **kwargs):
        super().__init__(**kwargs)
        self._work_dir = builtin_args.ENSOUL_WORK_DIR

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        # TODO: checks:
        # - check if the path may contain secrets
        # - check if the file format is readable
        try:
            p = Path(params.path)

            if not p.is_absolute():
                return ToolError(
                    message=(
                        f"`{params.path}` is not an absolute path. "
                        "You must provide an absolute path to read a file."
                    ),
                    brief="Invalid path",
                )

            if not p.exists():
                return ToolError(
                    message=f"`{params.path}` does not exist.",
                    brief="File not found",
                )
            if not p.is_file():
                return ToolError(
                    message=f"`{params.path}` is not a file.",
                    brief="Invalid path",
                )

            start_line = max(1, int(params.line_offset))
            max_lines: int = min(max(1, int(params.n_lines)), _MAX_LINES)

            # Read with streaming to support large files efficiently
            lines: list[str] = []
            async with aiofiles.open(p, encoding="utf-8", errors="replace") as f:
                current_line_no = 0
                async for line in f:
                    current_line_no += 1
                    if current_line_no < start_line:
                        continue
                    lines.append(_truncate_line(line))
                    if len(lines) >= max_lines:
                        break

            if len(lines) == 0:
                return ToolOk(output="", message="No lines read from file.")

            # Format output with line numbers like `cat -n`
            lines_with_no = []
            for line_num, line in zip(
                range(start_line, start_line + len(lines)), lines, strict=True
            ):
                # Use 6-digit line number width, right-aligned, with tab separator
                lines_with_no.append(f"{line_num:6d}\t{line}")

            # TODO: add message for EOF
            return ToolOk(
                output="\n".join(lines_with_no),
                message=(f"{len(lines)} lines read from file, starting from line {start_line}."),
            )
        except Exception as e:
            return ToolError(
                message=f"Failed to read {params.path}. Error: {e}",
                brief="Failed to read file",
            )
