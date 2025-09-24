"""Glob tool implementation."""

from pathlib import Path
from typing import override

from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType

from kimi_cli.agent import BuiltinSystemPromptArgs


class Glob(CallableTool):
    name: str = "Glob"
    description: str = (Path(__file__).parent / "glob.md").read_text()
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": (
                    "Glob pattern to match files/directories "
                    "(e.g., '*.py', 'src/**/*.js', 'test_*.txt')"
                ),
            },
            "directory": {
                "type": "string",
                "description": (
                    "Absolute path to the directory to search in (defaults to working directory)"
                ),
                "default": None,
            },
            "include_dirs": {
                "type": "boolean",
                "description": "Whether to include directories in results",
                "default": True,
            },
        },
        "required": ["pattern"],
    }

    def __init__(self, builtin_args: BuiltinSystemPromptArgs, **kwargs):
        super().__init__(**kwargs)
        self._work_dir = builtin_args.ENSOUL_WORK_DIR

    def _validate_pattern(self, pattern: str) -> ToolError | None:
        """Validate that the pattern is safe to use."""
        if pattern.startswith("**"):
            return ToolError(
                f"Pattern `{pattern}` starts with '**' which is not allowed. "
                "This would recursively search all directories and may include large directories "
                "like `node_modules`. Use more specific patterns like 'src/**/*.py' instead.",
                "Unsafe pattern",
            )
        return None

    def _validate_directory(self, directory: Path) -> ToolError | None:
        """Validate that the directory is safe to search."""
        try:
            resolved_dir = directory.resolve()
            resolved_work_dir = self._work_dir.resolve()

            # Ensure the directory is within work directory
            if not str(resolved_dir).startswith(str(resolved_work_dir)):
                return ToolError(
                    f"`{directory}` is outside the working directory. "
                    "You can only search within the working directory.",
                    "Directory outside working directory",
                )
            return None
        except Exception as e:
            return ToolError(f"Invalid directory: {e}", "Invalid directory")

    @override
    async def __call__(
        self,
        pattern: str,
        directory: str | None = None,
        include_dirs: bool = True,
    ) -> ToolReturnType:
        try:
            # Validate pattern safety
            pattern_error = self._validate_pattern(pattern)
            if pattern_error:
                return pattern_error

            dir_path = Path(directory) if directory else self._work_dir

            if not dir_path.is_absolute():
                return ToolError(
                    f"`{directory}` is not an absolute path. "
                    "You must provide an absolute path to search.",
                    "Invalid directory",
                )

            # Validate directory safety
            dir_error = self._validate_directory(dir_path)
            if dir_error:
                return dir_error

            if not dir_path.exists():
                return ToolError(
                    f"`{directory}` does not exist.",
                    "Directory not found",
                )
            if not dir_path.is_dir():
                return ToolError(
                    f"`{directory}` is not a directory.",
                    "Invalid directory",
                )

            # Perform the glob search - users can use ** directly in pattern
            matches = list(dir_path.glob(pattern))

            # Filter out directories if not requested
            if not include_dirs:
                matches = [p for p in matches if p.is_file()]

            # Sort for consistent output
            matches.sort()

            # Format results
            if not matches:
                return ToolOk(f"No files or directories found matching pattern `{pattern}`.")

            result_lines = [f"Found {len(matches)} matches for pattern `{pattern}`:"]
            result_lines.extend(f"  {p.relative_to(dir_path)}" for p in matches)

            return ToolOk("\n".join(result_lines))

        except Exception as e:
            return ToolError(f"Failed to search for pattern {pattern}. Error: {e}", "Glob failed")
