# Research – Textual Command Autocompletion Implementation

**Date:** 2025-12-08 12:14:02
**Owner:** claude
**Phase:** Research
**Git Commit:** 9a4915a4d2cd77831bd39b9b41343afbc987756d

## Goal
Research how to implement autocompletion for slash commands in the Textual TUI application, mapping existing command structure to autocompletion implementation patterns.

## Additional Search
- `grep -ri "autocomplete" .claude/` - No results found

## Findings

### Relevant Files & Why They Matter

#### Command System
- `/root/tunacode/src/tunacode/ui/commands/__init__.py` → Central command registry with all slash commands defined
  - Contains COMMANDS dictionary mapping command names to Command class instances
  - Commands: help, clear, yolo, model, branch, plan, theme, resume
  - Command base class with name, description, and usage properties
- `/root/tunacode/src/tunacode/ui/app.py:473` → Main TUI application with key event handling
  - on_key method processes user input
  - on_editor_submit_requested handles command execution at line 289

#### Existing Autocomplete Implementation
- `/root/tunacode/src/tunacode/ui/widgets/file_autocomplete.py` → Reference implementation for file path completion
  - Uses textual_autocomplete library (v4.0.6)
  - Triggered by `@` symbol
  - Extends AutoComplete widget with custom logic

#### Input Components
- `/root/tunacode/src/tunacode/ui/widgets/editor.py` → Custom Editor widget extending Input
  - Key handling at line 26
  - Posts EditorSubmitRequested message on Enter
- `/root/tunacode/src/tunacode/utils/parsing/command_parser.py` → Command parsing utilities
- `/root/tunacode/src/tunacode/utils/security/command.py` → Command security validation

### Current Command Structure
Commands use the following patterns:
- **Slash commands**: `/command [arguments]`
- **Shell commands**: `!command`
- **Special**: `exit` (no prefix)

### Key Patterns / Solutions Found

1. **textual-autocomplete Library Pattern** (Currently Used)
   - Project already has textual-autocomplete>=4.0.6 installed
   - FileAutoComplete provides working reference implementation
   - AutoComplete base class with three key methods:
     - `get_search_string()` - Extracts text to complete
     - `get_candidates()` - Returns dropdown items
     - `apply_completion()` - Applies selected completion

2. **Command Detection Strategy**
   - Trigger on `/` character (similar to `@` for files)
   - Extract text after `/` until cursor or space
   - Don't complete if space exists (command has arguments)
   - Show command descriptions in dropdown for better UX

3. **Integration Points**
   - Add CommandAutoComplete widget to app's compose() method
   - Place after Editor widget (same pattern as FileAutoComplete)
   - Import COMMANDS dictionary for candidate list

4. **Implementation Blueprint**
   ```python
   class CommandAutoComplete(AutoComplete):
       def get_search_string(self, target_state: TargetState) -> str:
           # Find last '/' before cursor
           # Return text after '/' until space

       def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
           # Filter COMMANDS dict by search string
           # Return DropdownItem with prefix="/"

       def apply_completion(self, value: str, state: TargetState) -> None:
           # Replace command part with completed value
           # Add space after completion
   ```

### Knowledge Gaps
- Whether commands with subcommands (like `/resume load`) should complete subcommands
- Integration with existing FileAutoComplete - should they be combined or separate?
- Performance impact of importing COMMANDS dict for each completion request
- Testing strategy for autocompletion functionality

## References
- Textual Autocomplete Documentation: Installed with textual-autocomplete package
- Textual Completion Guide: https://textual.textualize.io/guide/completion/
- FileAutoComplete implementation: `/root/tunacode/src/tunacode/ui/widgets/file_autocomplete.py`
- Command definitions: `/root/tunacode/src/tunacode/ui/commands/__init__.py`
- TUI App structure: `/root/tunacode/src/tunacode/ui/app.py`
