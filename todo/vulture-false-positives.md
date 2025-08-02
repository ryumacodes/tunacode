# Vulture False Positives

This document tracks known false positives from the vulture dead code detection tool that we've decided to keep in the codebase.

## False Positives

### src/tunacode/core/state.py:25
- Import: `from tunacode.core.tool_handler import ToolHandler` (in TYPE_CHECKING block)
- Usage: Used for type hints in the SessionState class
- Confidence: 90%
- Decision: Keep as-is since it's used for type annotations within TYPE_CHECKING blocks, which vulture cannot detect properly.

Lines where ToolHandler is used:
- Line 97: `self._tool_handler: Optional["ToolHandler"] = None`
- Line 104: `def tool_handler(self) -> Optional["ToolHandler"]:`
- Line 107: `def set_tool_handler(self, handler: "ToolHandler") -> None:`
