from pathlib import Path
from typing import override

import aiofiles
from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType

from kimi_cli.agent import BuiltinSystemPromptArgs


class WriteFile(CallableTool):
    name: str = "WriteFile"
    description: str = (Path(__file__).parent / "write.md").read_text()
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The absolute path to the file to write",
            },
            "content": {"type": "string", "description": "The content to write to the file"},
            "mode": {
                "type": "string",
                "description": "The mode to use to write to the file",
                "enum": ["overwrite", "append"],
                "default": "overwrite",
            },
        },
        "required": ["path", "content"],
    }

    def __init__(self, builtin_args: BuiltinSystemPromptArgs, **kwargs):
        super().__init__(**kwargs)
        self._work_dir = builtin_args.ENSOUL_WORK_DIR

    def _validate_path(self, path: Path) -> ToolError | None:
        """Validate that the path is safe to write."""
        # Check for path traversal attempts
        try:
            resolved_path = path.resolve()
            resolved_work_dir = self._work_dir.resolve()

            # Ensure the path is within work directory
            if not str(resolved_path).startswith(str(resolved_work_dir)):
                return ToolError(
                    f"`{path}` is outside the working directory. "
                    "You can only write files within the working directory.",
                    "Path outside working directory",
                )
            return None
        except Exception as e:
            return ToolError(f"Invalid path: {e}", "Invalid path")

    @override
    async def __call__(self, path: str, content: str, mode: str = "overwrite") -> ToolReturnType:
        # TODO: checks:
        # - check if the path may contain secrets
        # - check if the file format is writable
        try:
            p = Path(path)

            if not p.is_absolute():
                return ToolError(
                    f"`{path}` is not an absolute path. "
                    "You must provide an absolute path to write a file.",
                    "Invalid path",
                )

            # Validate path safety
            path_error = self._validate_path(p)
            if path_error:
                return path_error

            if not p.parent.exists():
                return ToolError(
                    f"`{path}` parent directory does not exist.",
                    "Parent directory not found",
                )

            # Validate mode parameter
            if mode not in ["overwrite", "append"]:
                return ToolError(
                    f"Invalid write mode: `{mode}`. Mode must be either 'overwrite' or 'append'.",
                    "Invalid write mode",
                )

            # Determine file mode for aiofiles
            file_mode = "w" if mode == "overwrite" else "a"

            # Write content to file
            async with aiofiles.open(p, mode=file_mode, encoding="utf-8") as f:
                await f.write(content)

            # Get file info for success message
            file_size = p.stat().st_size
            action = "overwritten" if mode == "overwrite" else "appended to"

            return ToolOk(
                f"File successfully {action}. Path: {path}. Current size: {file_size} bytes."
            )

        except Exception as e:
            return ToolError(f"Failed to write to {path}. Error: {e}", "Failed to write file")
