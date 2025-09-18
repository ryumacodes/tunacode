from pathlib import Path

import ripgrepy
from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType


# TODO: download ripgrep if not available
class Grep(CallableTool):
    name: str = "grep"
    description: str = (Path(__file__).parent / "grep.md").read_text()
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The regular expression pattern to search for in file contents",
            },
            "path": {
                "type": "string",
                "description": (
                    "File or directory to search in. Defaults to current working directory. "
                    "If specified, it must be an absolute path."
                ),
            },
            "glob": {
                "type": "string",
                "description": (
                    "Glob pattern to filter files (e.g. `*.js`, `*.{ts,tsx}`). "
                    "No filter by default."
                ),
            },
            "output_mode": {
                "type": "string",
                "enum": ["content", "files_with_matches", "count_matches"],
                "description": (
                    "`content`: Show matching lines (supports `before_context`, `after_context` "
                    " `context`, `line_number`, `head_limit`); "
                    "`files_with_matches`: Show file paths (supports `head_limit`); "
                    "`count_matches`: Show total number of matches. "
                    "Defaults to `files_with_matches`."
                ),
            },
            "before_context": {
                "type": "number",
                "description": (
                    "Number of lines to show before each match (the `-B` option). "
                    "Requires `output_mode` to be `content`."
                ),
            },
            "after_context": {
                "type": "number",
                "description": (
                    "Number of lines to show after each match (the `-A` option). "
                    "Requires `output_mode` to be `content`."
                ),
            },
            "context": {
                "type": "number",
                "description": (
                    "Number of lines to show before and after each match (the `-C` option). "
                    "Requires `output_mode` to be `content`."
                ),
            },
            "line_number": {
                "type": "boolean",
                "description": (
                    "Show line numbers in output (the `-n` option). "
                    "Requires `output_mode` to be `content`."
                ),
            },
            "ignore_case": {
                "type": "boolean",
                "description": "Case insensitive search (the `-i` option).",
            },
            "type": {
                "type": "string",
                "description": (
                    "File type to search. Examples: py, rust, js, ts, go, java, etc. "
                    "More efficient than `glob` for standard file types."
                ),
            },
            "head_limit": {
                "type": "number",
                "description": (
                    "Limit output to first N lines, equivalent to `| head -N`. "
                    "Works across all output modes: content (limits output lines), "
                    "files_with_matches (limits file paths), count_matches (limits count entries). "
                    "By default, no limit is applied."
                ),
            },
            "multiline": {
                "type": "boolean",
                "description": (
                    "Enable multiline mode where `.` matches newlines and patterns can span "
                    "lines (the `-U` and `--multiline-dotall` options). "
                    "By default, multiline mode is disabled."
                ),
            },
        },
        "required": ["pattern"],
    }

    async def __call__(
        self,
        pattern: str,
        path: str = ".",
        glob: str | None = None,
        output_mode: str = "files_with_matches",
        head_limit: int | None = None,
        # Content display options
        before_context: int | None = None,
        after_context: int | None = None,
        context: int | None = None,
        line_number: bool = False,
        # Search options
        ignore_case: bool = False,
        type: str | None = None,
        multiline: bool = False,
    ) -> ToolReturnType:
        try:
            # Initialize ripgrep with pattern and path
            rg = ripgrepy.Ripgrepy(pattern, path)

            # Apply search options
            if ignore_case:
                rg = rg.ignore_case()
            if multiline:
                rg = rg.multiline().multiline_dotall()

            # Content display options (only for content mode)
            if output_mode == "content":
                if before_context is not None:
                    rg = rg.before_context(before_context)
                if after_context is not None:
                    rg = rg.after_context(after_context)
                if context is not None:
                    rg = rg.context(context)
                if line_number:
                    rg = rg.line_number()

            # File filtering options
            if glob:
                rg = rg.glob(glob)
            if type:
                rg = rg.type_(type)

            # Set output mode
            if output_mode == "files_with_matches":
                rg = rg.files_with_matches()
            elif output_mode == "count_matches":
                rg = rg.count_matches()

            # Execute search
            result = rg.run()

            # Get results
            output = result.as_string

            # Apply head limit if specified
            if head_limit is not None:
                lines = output.split("\n")
                if len(lines) > head_limit:
                    lines = lines[:head_limit]
                    output = "\n".join(lines)
                    if output_mode in ["content", "files_with_matches", "count_matches"]:
                        output += f"\n... (results truncated to {head_limit} lines)"

            if not output:
                return ToolOk("<system-message>No matches found</system-message>")
            return ToolOk(output)

        except Exception as e:
            return ToolError(
                f"<system-message>Failed to grep. Error: {str(e)}</system-message>",
                "Failed to grep",
            )
