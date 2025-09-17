from pathlib import Path
from typing import override

import aiofiles
from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType

from kimi_cli.agent import BuiltinSystemPromptArgs

_TEMPLATE = """\
{n_lines} lines read from {path}, starting from line {line_offset}.
Content:
{content}\
"""


class ReadFile(CallableTool):
    name: str = "read_file"
    description: str = (Path(__file__).parent / "read.md").read_text()
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The absolute path to the file to read",
            },
            "line_offset": {
                "type": "number",
                "default": 1,
                "description": (
                    "The line number to start reading from. "
                    "By default read from the beginning of the file. "
                    "Set this when the file is too large to read at once."
                ),
            },
            "n_lines": {
                "type": "number",
                "default": None,
                "description": (
                    "The number of lines to read. "
                    "By default read to the end of the file. "
                    "Set this when the file is too large to read at once."
                ),
            },
        },
        "required": ["path"],
    }

    def __init__(self, builtin_args: BuiltinSystemPromptArgs, **kwargs):
        super().__init__(**kwargs)
        self._work_dir = builtin_args.ENSOUL_WORK_DIR

    def _validate_path(self, path: Path) -> ToolError | None:
        """Validate that the path is safe to read."""
        # Check for path traversal attempts
        try:
            resolved_path = path.resolve()
            resolved_work_dir = self._work_dir.resolve()

            # Ensure the path is within work directory
            if not str(resolved_path).startswith(str(resolved_work_dir)):
                return ToolError(
                    f"`{path}` is outside the working directory. "
                    "You can only read files within the working directory.",
                    "Path outside working directory",
                )
            return None
        except Exception as e:
            return ToolError(f"Invalid path: {e}", "Invalid path")

    @override
    async def __call__(
        self,
        path: str,
        line_offset: int = 1,
        n_lines: int | None = None,
    ) -> ToolReturnType:
        # TODO: checks:
        # - check if the path may contain secrets
        # - check if the file format is readable
        # - check if the line_offset and n_lines are valid
        # - check if there are lines that are too long
        try:
            p = Path(path)

            if not p.is_absolute():
                return ToolError(
                    f"`{path}` is not an absolute path. "
                    "You must provide an absolute path to read a file.",
                    "Invalid path",
                )

            # Validate path safety
            path_error = self._validate_path(p)
            if path_error:
                return path_error

            if not p.exists():
                return ToolError(
                    f"`{path}` does not exist.",
                    "File not found",
                )
            if not p.is_file():
                return ToolError(
                    f"`{path}` is not a file.",
                    "Invalid path",
                )

            start_line = max(1, int(line_offset))
            max_lines: int | None = None if n_lines is None else max(1, int(n_lines))

            # Read with streaming to support large files efficiently
            lines: list[str] = []
            async with aiofiles.open(p, encoding="utf-8", errors="replace") as f:
                current_line_no = 0
                async for line in f:
                    current_line_no += 1
                    if current_line_no < start_line:
                        continue
                    lines.append(line)
                    if max_lines is not None and len(lines) >= max_lines:
                        break

            if len(lines) == 0:
                return ToolOk(
                    f"No lines read from {path}.",
                )

            return ToolOk(
                _TEMPLATE.format(
                    n_lines=len(lines),
                    path=path,
                    line_offset=start_line,
                    content="".join(lines),
                )
            )
        except Exception as e:
            return ToolError(f"Failed to read {path}. Error: {e}", "Failed to read file")
