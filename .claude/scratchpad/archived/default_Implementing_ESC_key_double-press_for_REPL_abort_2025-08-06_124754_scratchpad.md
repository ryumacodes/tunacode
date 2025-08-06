# Implementing ESC key double-press for REPL abort
_Started: 2025-08-06 12:47:04_
_Agent: default

[1] Found existing ESC handler in src/tunacode/ui/keybindings.py:33-81 with separate tracking
[2] Issue: ESC handler had separate tracking from Ctrl+C, causing inconsistent messages
[3] Simplified ESC handler to immediately raise KeyboardInterrupt for unified abort tracking
[4] Updated REPL message from Hit Ctrl+C again to exit to Hit ESC or Ctrl+C again to exit
[5] Renamed ctrl_c_pressed to abort_pressed in repl.py for clarity
[6] Updated tests to expect new warning message in test_keyboard_interrupts.py and test_characterization_repl.py
[7] All tests passing, committed with message: fix: unify ESC and Ctrl+C abort handling in REPL
