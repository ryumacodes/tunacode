# ESC Double-Press REPL Abort Analysis
_Started: 2025-08-06 12:51:37_
_Agent: code-synthesis-analyzer

[1] [1] Examined src/tunacode/ui/keybindings.py - ESC handler now immediately raises KeyboardInterrupt (line 48)
[2] [2] Examined src/tunacode/cli/repl.py - unified abort_pressed flag tracks both ESC and Ctrl+C (line 253)
[3] [3] Found UserAbortError is raised in ui/prompt_manager.py when KeyboardInterrupt occurs (line 209)
[4] [4] multiline_input shows Esc twice to cancel in placeholder (line 84) - inconsistent with single ESC behavior
[5] [5] Previous ESC implementation had double-press logic with warning, new implementation immediately raises KeyboardInterrupt
[6] [6] Tests expect Hit ESC or Ctrl+C again to exit warning message (line 55)
[7] [7] No specific tests found for ESC key double-press behavior - tests only cover UserAbortError from Ctrl+C
[8] [8] Key flow: ESC key -> KeyboardInterrupt -> caught by prompt_manager -> converted to UserAbortError -> caught by REPL
