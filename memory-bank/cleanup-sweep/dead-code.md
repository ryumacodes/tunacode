# Dead Code Detection Report

**Generated**: 2025-12-14
**Scope**: /home/tuna/tunacode/src/tunacode

---

## Executive Summary

Comprehensive scan of `/home/tuna/tunacode/src/tunacode` identifying unused exports, unreferenced constants, and potential cleanup candidates. This analysis focuses on exported items that have zero imports elsewhere in the codebase.

---

## 1. Unused Constants in `/home/tuna/tunacode/src/tunacode/constants.py`

### Backward Compatibility Tool Constants (Lines 61-68)

**UNUSED - All 7 constants have zero references:**

```python
TOOL_READ_FILE = ToolName.READ_FILE      # Line 62
TOOL_WRITE_FILE = ToolName.WRITE_FILE    # Line 63
TOOL_UPDATE_FILE = ToolName.UPDATE_FILE  # Line 64
TOOL_BASH = ToolName.BASH                # Line 65
TOOL_GREP = ToolName.GREP                # Line 66
TOOL_LIST_DIR = ToolName.LIST_DIR        # Line 67
TOOL_GLOB = ToolName.GLOB                # Line 68
```

**Evidence**: Grep search shows these are only defined, never referenced. The `ToolName` enum is used instead throughout the codebase.

---

### Command Constants (Lines 84-89)

**UNUSED - All 6 command string constants:**

```python
CMD_HELP = "/help"    # Line 84
CMD_CLEAR = "/clear"  # Line 85
CMD_YOLO = "/yolo"    # Line 86
CMD_MODEL = "/model"  # Line 87
CMD_EXIT = "exit"     # Line 88
CMD_QUIT = "quit"     # Line 89
```

**Evidence**: These are never imported or used. Commands are handled via hardcoded strings in command handlers.

---

### Command Description Constants (Lines 92-96)

**UNUSED - All 5 description constants:**

```python
DESC_HELP = "Show this help message"                # Line 92
DESC_CLEAR = "Clear the conversation history"       # Line 93
DESC_YOLO = "Toggle confirmation prompts on/off"    # Line 94
DESC_MODEL = "List available models"                # Line 95
DESC_EXIT = "Exit the application"                  # Line 96
```

**Evidence**: Zero references found. Command descriptions are hardcoded in command classes.

---

### Command Configuration (Line 99)

**UNUSED:**

```python
COMMAND_PREFIX = "/"  # Line 99
```

**Evidence**: Never imported or used. The "/" prefix is hardcoded where needed.

---

### File Pattern Constants (Line 16)

**UNUSED:**

```python
GUIDE_FILE_PATTERN = "{name}.md"  # Line 16
```

**Evidence**: Zero references. Only `ENV_FILE` (line 18) is actually used.

---

### UI Constants (Lines 150-158)

**UNUSED - Most UI text constants:**

```python
UI_PROMPT_PREFIX = '<style fg="#00d7ff"><b>> </b></style>'  # Line 150 - UNUSED
UI_DARKGREY_OPEN = "<darkgrey>"                              # Line 152 - UNUSED
UI_DARKGREY_CLOSE = "</darkgrey>"                            # Line 153 - UNUSED
UI_BOLD_OPEN = "<bold>"                                      # Line 154 - UNUSED
UI_BOLD_CLOSE = "</bold>"                                    # Line 155 - UNUSED
UI_KEY_ENTER = "Enter"                                       # Line 156 - UNUSED
UI_KEY_ESC_ENTER = "Esc + Enter"                             # Line 157 - UNUSED
```

**Evidence**: Only `UI_THINKING_MESSAGE` (line 151) is used.

---

### Panel Title Constants (Lines 160-163)

**UNUSED - All panel title constants:**

```python
PANEL_ERROR = "Error"                        # Line 160
PANEL_MESSAGE_HISTORY = "Message History"    # Line 161
PANEL_MODELS = "Models"                      # Line 162
PANEL_AVAILABLE_COMMANDS = "Available Commands"  # Line 163
```

**Evidence**: Zero references. Panel titles are hardcoded where used.

---

### Error Message Constants (Lines 166-182)

**UNUSED - Most error message constants:**

```python
ERROR_PROVIDER_EMPTY = "Provider number cannot be empty"      # Line 166 - UNUSED
ERROR_INVALID_PROVIDER = "Invalid provider number"            # Line 167 - UNUSED
ERROR_FILE_NOT_FOUND = "Error: File not found at '{filepath}'."  # Line 168 - UNUSED
ERROR_FILE_DECODE = "Error reading file '{filepath}': ..."    # Line 170 - UNUSED
ERROR_FILE_DECODE_DETAILS = "It might be a binary file..."    # Line 171 - UNUSED
ERROR_COMMAND_NOT_FOUND = "Error: Command not found..."       # Line 172 - UNUSED
ERROR_COMMAND_EXECUTION = "Error: Command not found or..."    # Lines 173-175 - UNUSED
ERROR_DIR_TOO_LARGE = "Error: Directory '{path}' expansion..."  # Lines 177-179 - UNUSED
ERROR_DIR_TOO_MANY_FILES = "Error: Directory '{path}' ..."    # Lines 180-182 - UNUSED
```

**Used**: Only `ERROR_FILE_TOO_LARGE` (line 169) is used in `/home/tuna/tunacode/src/tunacode/tools/read_file.py:8,36`.

---

### Command Output Constants (Lines 185-188)

**UNUSED - Most command output formatting constants:**

```python
CMD_OUTPUT_NO_OUTPUT = "No output."                          # Line 185 - UNUSED
CMD_OUTPUT_NO_ERRORS = "No errors."                          # Line 186 - UNUSED
CMD_OUTPUT_FORMAT = "STDOUT:\n{output}\n\nSTDERR:\n{error}" # Line 187 - UNUSED
```

**Used**: Only `CMD_OUTPUT_TRUNCATED` (line 188) is used.

---

### Message/Version Constants (Lines 192-194)

**UNUSED:**

```python
MSG_UPDATE_AVAILABLE = "Update available: v{latest_version}"              # Line 192
MSG_UPDATE_INSTRUCTION = "Exit, and run: [bold]pip install --upgrade..." # Line 193
MSG_VERSION_DISPLAY = "TunaCode CLI {version}"                            # Line 194
```

**Used**: Only `MSG_FILE_SIZE_LIMIT` (line 195) is used.

---

## 2. Unused Type Aliases in `/home/tuna/tunacode/src/tunacode/types.py`

**Lines 27-168: Multiple type aliases with zero usage:**

```python
EnvConfig = dict[str, str]                    # Line 27 - UNUSED
ModelRegistry = dict[str, ModelConfig]        # Line 51 - UNUSED
ToolStartCallback = Callable[[str], None]     # Line 60 - UNUSED
UICallback = Callable[[str], Awaitable[None]] # Line 90 - UNUSED
UIInputCallback = Callable[[str, str], ...]   # Line 91 - UNUSED
AgentConfig = dict[str, Any]                  # Line 97 - UNUSED
AgentName = str                               # Line 98 - UNUSED
CommandArgs = list[str]                       # Line 132 - UNUSED
CommandResult = Any | None                    # Line 133 - UNUSED
FileContent = str                             # Line 146 - UNUSED
FileEncoding = str                            # Line 147 - UNUSED
FileDiff = tuple[str, str]                    # Line 148 - UNUSED
FileSize = int                                # Line 149 - UNUSED
LineNumber = int                              # Line 150 - UNUSED
ErrorContext = dict[str, Any]                 # Line 152 - UNUSED
AsyncFunc = Callable[..., Awaitable[Any]]     # Line 156 - UNUSED
AsyncToolFunc = Callable[..., Awaitable[str]] # Line 157 - UNUSED
AsyncVoidFunc = Callable[..., Awaitable[None]] # Line 158 - UNUSED
UpdateOperation = dict[str, Any]              # Line 160 - UNUSED
DiffLine = str                                # Line 161 - UNUSED
DiffHunk = list[DiffLine]                     # Line 162 - UNUSED
ValidationResult = bool | str                 # Line 164 - UNUSED
Validator = Callable[[Any], ValidationResult] # Line 165 - UNUSED
TokenCount = int                              # Line 167 - UNUSED
CostAmount = float                            # Line 168 - UNUSED
```

---

## 3. Unused Exported Functions

### `/home/tuna/tunacode/src/tunacode/configuration/key_descriptions.py`

**Lines 212-260**: Four exported functions with zero imports

```python
def get_key_description(key_path: str) -> KeyDescription | None:  # Line 212
def get_service_type_for_api_key(key_name: str) -> str | None:   # Line 217
def get_categories() -> dict[str, list[KeyDescription]]:          # Line 229
def get_configuration_glossary() -> str:                          # Line 237
```

**Evidence**: Grep search for `from tunacode.configuration.key_descriptions import` returns no matches.

---

### `/home/tuna/tunacode/src/tunacode/utils/parsing/retry.py`

**Lines 11-82, 117-146**: Two exported functions with zero external imports

```python
def retry_on_json_error(...) -> Callable:  # Line 11 - decorator
async def retry_json_parse_async(...)     # Line 117 - async variant
```

**Evidence**:
- `retry_on_json_error` is only used internally within the same file
- `retry_json_parse_async` has no usage anywhere
- Only `retry_json_parse` (line 85) is actually imported externally

---

## 4. Summary Statistics

| Category | Unused Items | File(s) |
|----------|--------------|---------|
| **Constants** | 47+ constants | `constants.py` |
| **Type Aliases** | 26 type aliases | `types.py` |
| **Functions** | 6 functions | `key_descriptions.py`, `retry.py` |

### Total: ~79+ unused definitions

---

## 5. No Issues Found

- **No large commented code blocks** (10+ lines) detected
- **No unused dependencies** in pyproject.toml - all are actively used
- **No orphaned Python files** - all .py files are imported somewhere

---

## 6. Recommendations

### High Priority (Safe to Remove)
1. **Lines 61-68** in `constants.py`: Remove `TOOL_*` backward compatibility constants
2. **Lines 84-99** in `constants.py`: Remove all `CMD_*`, `DESC_*`, and `COMMAND_PREFIX` constants
3. **Lines 150-163** in `constants.py`: Remove unused UI and panel constants
4. **Lines 166-194** in `constants.py`: Remove unused error/message constants (keep only used ones)

### Medium Priority
1. **All unused type aliases** in `types.py` (26 items)
2. **`key_descriptions.py`** (lines 212-260): Review if functions are intended for future use

### Low Priority
1. **`retry.py`** (lines 11-82, 117-146): The decorator and async variant may be useful for future retry logic

---

**End of Report**
