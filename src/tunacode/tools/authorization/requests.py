from __future__ import annotations

import difflib
import os

from tunacode.tools.utils.text_match import replace
from tunacode.types import ToolArgs, ToolConfirmationRequest, ToolName

MAX_PREVIEW_LINES = 100


def _generate_creation_diff(filepath: str, content: str) -> str:
    """Generate a unified diff for new file creation."""
    lines = content.splitlines(keepends=True)
    total_lines = len(lines)

    truncated = total_lines > MAX_PREVIEW_LINES
    if truncated:
        lines = lines[:MAX_PREVIEW_LINES]

    diff_parts = [
        "--- /dev/null\n",
        f"+++ b/{filepath}\n",
        f"@@ -0,0 +1,{len(lines)} @@\n",
    ]

    for line in lines:
        if not line.endswith("\n"):
            line += "\n"
        diff_parts.append(f"+{line}")

    if truncated:
        diff_parts.append(f"\n... ({total_lines - MAX_PREVIEW_LINES} more lines)\n")

    return "".join(diff_parts)


class ConfirmationRequestFactory:
    """Create structured confirmation requests for UI surfaces."""

    def create(self, tool_name: ToolName, args: ToolArgs) -> ToolConfirmationRequest:
        filepath = args.get("filepath")
        diff_content: str | None = None

        if tool_name == "update_file" and filepath and os.path.exists(filepath):
            target = args.get("target")
            patch = args.get("patch")
            if target and patch:
                try:
                    with open(filepath, encoding="utf-8") as f:
                        original = f.read()

                    # Attempt to generate what the new content will look like
                    new_content = replace(original, target, patch, replace_all=False)

                    diff_lines = list(
                        difflib.unified_diff(
                            original.splitlines(keepends=True),
                            new_content.splitlines(keepends=True),
                            fromfile=f"a/{filepath}",
                            tofile=f"b/{filepath}",
                        )
                    )
                    if diff_lines:
                        diff_content = "".join(diff_lines)
                except Exception:
                    # If anything fails (file read, fuzzy match, etc), we just don't show the diff
                    pass

        elif tool_name == "write_file" and filepath:
            content = args.get("content", "")
            if content:
                diff_content = _generate_creation_diff(filepath, content)

        return ToolConfirmationRequest(
            tool_name=tool_name, args=args, filepath=filepath, diff_content=diff_content
        )
