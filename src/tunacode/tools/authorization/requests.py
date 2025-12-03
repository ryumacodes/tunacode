from __future__ import annotations

from tunacode.types import ToolArgs, ToolConfirmationRequest, ToolName


class ConfirmationRequestFactory:
    """Create structured confirmation requests for UI surfaces."""

    def create(self, tool_name: ToolName, args: ToolArgs) -> ToolConfirmationRequest:
        filepath = args.get("filepath")
        return ToolConfirmationRequest(tool_name=tool_name, args=args, filepath=filepath)
