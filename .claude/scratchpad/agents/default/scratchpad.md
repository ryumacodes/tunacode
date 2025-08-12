# Always-On Model/Context/Price Display Implementation
_Started: 2025-08-12 15:31:29_
_Agent: default

[1] Starting implementation - found key files: src/tunacode/cli/repl.py:417-421 (show_context), src/tunacode/core/token_usage/usage_tracker.py:44 (display_summary), and session summary at repl.py:504-516
[2] Updated repl.py:421-431 to always show context and session cost without show_thoughts gate
[3] Added UsageTracker instantiation in process_request and wired to both streaming and non-streaming agent.process_request calls
[4] Removed show_thoughts gate from session summary - now always displays if session_total_usage has data
[5] Reviewed usage_tracker.py - logic is correct. Session state always updates, detailed display only when show_thoughts enabled. Added clarifying comments.
[6] Fixed test_repl_initialization.py - updated tests to expect context always shown, startup message only on first run
[7] Implementation complete! All tests passing. Pre-existing test failure in test_tool_batching_retry.py confirmed unrelated to our changes.
