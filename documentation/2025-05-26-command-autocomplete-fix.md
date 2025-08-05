# Command Autocomplete Fix
**Date:** 2025-05-26
**Issue:** Slash command autocomplete not working when typing `/`

## Problem Description
When typing `/` in the REPL, command suggestions (like `/tools`, `/help`, `/clear`) were not appearing. The autocomplete was only working for file references using the `@` syntax.

## Root Cause
The input system was missing command completion functionality:

1. **Missing CommandCompleter**: Only `FileReferenceCompleter` existed for `@file` syntax
2. **No command registry integration**: The input system had no way to know what commands were available
3. **Single-purpose completer**: `multiline_input()` was only using file completion, not command completion

## Solution Implemented

### 1. Created CommandCompleter class
Added a new completer in `ui/completers.py` that:
- Detects when user types `/` at the beginning of a line
- Fetches available commands from the CommandRegistry
- Provides completion suggestions for matching commands

### 2. Created merged completer
Used `merge_completers()` to combine both:
- `CommandCompleter` for slash commands
- `FileReferenceCompleter` for @file references

### 3. Updated input system
Modified `ui/input.py`:
- Changed `multiline_input()` to accept a `command_registry` parameter
- Updated it to use `create_completer()` instead of just `FileReferenceCompleter()`

### 4. Connected command registry
Updated `cli/repl.py`:
- Passed `_command_registry` to `multiline_input()` call
- This gives the completer access to all registered commands

## Files Modified
- `/home/tuna/sidekick-cli/src/tunacode/ui/completers.py` - Added CommandCompleter class and create_completer function
- `/home/tuna/sidekick-cli/src/tunacode/ui/input.py` - Updated imports and multiline_input function
- `/home/tuna/sidekick-cli/src/tunacode/cli/repl.py` - Passed command registry to multiline_input

## Result
Now when typing `/` followed by any letters, the system shows autocomplete suggestions for all available commands like `/help`, `/clear`, `/dump`, `/yolo`, `/undo`, `/branch`, `/tunaCode`, `/compact`, `/model`, etc.
