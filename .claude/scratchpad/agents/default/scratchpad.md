# UI Architecture Documentation
_Started: 2025-08-07 12:55:15_
_Agent: default

[1] Found UI directory structure at src/tunacode/ui/ with key components: output.py, panels.py, console.py, input.py
[2] Key UI components found: StreamingAgentPanel (lines 81-166) handles progressive display with Live updates, spinner function (output.py:112-133) shows thinking state
[3] Found main REPL loop at repl.py:250-350. Process_request function (lines 98-243) handles agent requests with streaming support
[4] REPL components are modularized: output_display.py handles agent output, tool_executor.py manages tool confirmations
[5] Tool confirmations use ToolUI class (tool_ui.py) which renders panels with styled borders and handles user approval flow
[6] StateManager (state.py:96) and SessionState (state.py:31) track UI state including spinner, streaming_panel, tool_calls, and operation_cancelled
[7] Main entry point at cli/main.py uses typer CLI framework, starts with banner display, initializes ToolHandler and StateManager, then enters REPL
[8] UI_COLORS defined at constants.py:101-111 with modern color scheme: primary=#00d7ff (bright cyan), warning=#f59e0b (amber), etc.
[9] Key bindings at keybindings.py handle Enter (submit), Esc+Enter (newline), Esc (abort/cancel) interactions
[10] CommandRegistry at commands/registry.py manages all slash commands with categories (system, debug, development, etc)
[11] create_sync_wrapper decorator (decorators.py) allows async UI functions to have sync versions attached as .sync attribute
