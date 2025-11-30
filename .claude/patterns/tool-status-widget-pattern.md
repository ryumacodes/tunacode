# Tool Status Widget Pattern

**Component**: cli.textual_repl
**Type**: UI Pattern
**Status**: Blueprint (not yet implemented)

## Problem
Real-time tool activity feedback lost after promptkit->Textual migration.

## Solution Pattern
1. Define `ToolStatusUpdate(Message)` with status string
2. Create `ToolStatusBar(Static)` widget
3. Add `tool_status_callback: UICallback` to `process_request()`
4. Replace `ui.update_spinner_message()` with callback in `node_processor.py`

## Key Files
- `cli/widgets.py` - Widget definition
- `cli/textual_repl.py` - App integration, callback builder
- `core/agents/agent_components/node_processor.py` - Status source

## Callback Type
```python
UICallback = Callable[[str], Awaitable[None]]  # types.py:135
```

## See Also
- `memory-bank/research/2025-11-29_tool-activity-display-blueprint.md`
