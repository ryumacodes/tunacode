# Research - Utils Directory Architecture Mapping

**Date:** 2025-12-01
**Owner:** Agent
**Phase:** Research

## Goal

Comprehensive mapping of the `src/tunacode/utils/` directory structure, documenting all 17 utility modules, their purposes, exports, dependencies, and cross-module interactions.

## Directory Overview

```
src/tunacode/utils/
├── __init__.py              # Empty - forces explicit imports
├── api_key_validation.py    # API key validation for LLM providers
├── completion_utils.py      # File path autocomplete for UI
├── config_comparator.py     # Configuration difference analysis
├── diff_utils.py            # Unified diff generation with Rich styling
├── file_utils.py            # File system utilities (DotDict, capture_stdout)
├── import_cache.py          # Lazy module import caching
├── json_utils.py            # Robust JSON parsing with recovery
├── message_utils.py         # Polymorphic message content extraction
├── models_registry.py       # LLM model registry with API caching
├── retry.py                 # Retry mechanisms with exponential backoff
├── security.py              # Command injection prevention
├── system.py                # System utilities (paths, gitignore, cleanup)
├── text_utils.py            # Text processing and @file expansion
├── token_counter.py         # Token estimation using tiktoken
├── tool_descriptions.py     # Human-readable tool operation descriptions
└── user_configuration.py    # User config persistence with fingerprinting
```

## Module Categories

### 1. Core I/O & Data Manipulation

| Module | LOC | Purpose | Key Exports |
|--------|-----|---------|-------------|
| `file_utils.py` | 42 | System utilities | `DotDict`, `capture_stdout()` |
| `text_utils.py` | 223 | Text processing, @file expansion | `key_to_title()`, `ext_to_lang()`, `expand_file_refs()` |
| `json_utils.py` | 207 | JSON parsing with recovery | `safe_json_parse()`, `split_concatenated_json()`, `ConcatenatedJSONError` |
| `diff_utils.py` | 70 | Diff generation & styling | `render_file_diff()` |

### 2. API & Model Management

| Module | LOC | Purpose | Key Exports |
|--------|-----|---------|-------------|
| `api_key_validation.py` | 93 | Provider API key validation | `validate_api_key_for_model()`, `get_configured_providers()` |
| `models_registry.py` | 594 | Model metadata from models.dev | `ModelsRegistry`, `ModelInfo`, `ModelCapabilities` |
| `completion_utils.py` | 31 | File path autocomplete | `textual_complete_paths()`, `replace_token()` |

### 3. Configuration & System

| Module | LOC | Purpose | Key Exports |
|--------|-----|---------|-------------|
| `user_configuration.py` | 132 | Config persistence with fingerprinting | `load_config()`, `save_config()`, `set_default_model()` |
| `config_comparator.py` | 340 | Config difference analysis | `ConfigComparator`, `ConfigAnalysis`, `create_config_report()` |
| `system.py` | 332 | System paths, gitignore, cleanup | `get_tunacode_home()`, `list_cwd()`, `cleanup_session()` |

### 4. Message & Token Handling

| Module | LOC | Purpose | Key Exports |
|--------|-----|---------|-------------|
| `message_utils.py` | 29 | Polymorphic content extraction | `get_message_content()` |
| `token_counter.py` | 92 | Token estimation via tiktoken | `estimate_tokens()`, `get_encoding()` |
| `tool_descriptions.py` | 115 | UI-friendly tool descriptions | `get_tool_description()`, `get_batch_description()` |

### 5. Infrastructure & Cross-Cutting

| Module | LOC | Purpose | Key Exports |
|--------|-----|---------|-------------|
| `retry.py` | 163 | Retry with exponential backoff | `retry_on_json_error`, `retry_json_parse()`, `retry_json_parse_async()` |
| `security.py` | 209 | Command injection prevention | `validate_command_safety()`, `safe_subprocess_run()`, `CommandSecurityError` |
| `import_cache.py` | 11 | Lazy module import caching | `lazy_import()` |

## Key Architectural Patterns

### 1. Fingerprint-Based Caching (`user_configuration.py:40-43`)
```python
_config_fingerprint = None  # SHA1 hash of last loaded config
_config_cache = None        # Cached config dictionary
```
- Computes SHA1 of raw config file content
- Fast-path returns cached config if fingerprint matches
- Avoids redundant JSON parsing on repeated access

### 2. Three-Tier Fallback (`models_registry.py:387-418`)
```
1. Valid cache (< 24 hours) -> Return cached data
2. API fetch from models.dev -> Cache and return
3. Expired cache fallback -> Return with warning
4. Hardcoded fallback -> Popular models as last resort
```

### 3. Defense in Depth (`security.py:71-105`)
- **Layer 1:** Critical patterns always blocked (rm -rf /, sudo rm, fork bombs)
- **Layer 2:** Shell metacharacters conditionally blocked
- **Layer 3:** Targeted rm-injection patterns blocked

### 4. Smart Decorator Pattern (`retry.py:94-97`)
```python
if asyncio.iscoroutinefunction(func):
    return async_wrapper
return sync_wrapper
```
- Auto-detects sync vs async functions
- Single decorator works for both execution models

### 5. Polymorphic Message Handling (`message_utils.py:6-29`)
- Handles strings, dicts with `content`/`thought` keys
- Handles objects with `.content` or `.parts` attributes
- Recursive flattening for nested structures

## Cross-Module Dependencies

```
                    ┌─────────────────────────────────────────┐
                    │            constants.py                  │
                    │  (MAX_FILE_SIZE, READ_ONLY_TOOLS, etc.) │
                    └───────────────┬──────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   text_utils.py  │    │   json_utils.py  │    │  models_registry │
│  (file limits)   │    │ (tool safety)    │    │    (pydantic)    │
└──────────────────┘    └──────────────────┘    └──────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ message_utils.py │───▶│ token_counter.py │───▶│    tiktoken      │
│(content extract) │    │(token estimate)  │    │  (LRU cached)    │
└──────────────────┘    └──────────────────┘    └──────────────────┘

┌──────────────────┐    ┌──────────────────┐
│   security.py    │───▶│   subprocess     │
│(validate+wrap)   │    │ (safe execution) │
└──────────────────┘    └──────────────────┘
```

## Data Flows

### Token Counting Flow
```
SessionState.messages
    ↓
get_message_content(msg)  [message_utils.py:6]
    ↓ (extracts text from various formats)
Joined content string
    ↓
estimate_tokens(content)  [token_counter.py:58]
    ↓ (tiktoken or 4-char fallback)
SessionState.total_tokens  [state.py:97]
```

### Configuration Load Flow
```
load_config()  [user_configuration.py:32]
    ↓
ApplicationSettings().paths.config_file
    ↓
compute_config_fingerprint()  [line 26]
    ↓
Cache hit? → Return _config_cache
    ↓ (miss)
JSON parse + update cache
    ↓
_ensure_onboarding_defaults()  [line 94]
    ↓
Return UserConfig dict
```

### File Reference Expansion Flow
```
User input: "@src/file.py"
    ↓
expand_file_refs(text)  [text_utils.py:52]
    ↓
Regex match @references
    ↓
_read_and_format_file()  [line 203]
    ↓
ext_to_lang() for syntax highlighting
    ↓
Code fence formatted output
```

## Usage in Codebase

| Module | Imported By | Purpose |
|--------|-------------|---------|
| `retry_json_parse_async` | `core/agents/utils.py:23` | Retry LLM response parsing |
| `retry_json_parse` | `cli/command_parser.py:16` | Retry command parsing |
| `safe_subprocess_popen` | `tools/run_command.py:30` | Secure command execution |
| `get_message_content` | `core/state.py:23` | Token counting |
| `estimate_tokens` | `core/state.py:24` | Token counting |
| `DotDict` | `core/agents/main.py:30` | Config access |
| `validate_api_key_for_model` | `agent_config.py` | API key validation |

## Key Design Decisions

1. **Empty `__init__.py`**: Forces explicit imports, clear dependency tracking
2. **Fail-Fast Error Handling**: Custom exceptions with context (`ConfigurationError`, `CommandSecurityError`, `ConcatenatedJSONError`)
3. **Graceful Degradation**: Fallbacks for tiktoken, gitignore, cache misses
4. **Permission Safety**: Config dir created with mode 0o700
5. **LRU Caching**: Tiktoken encodings cached to avoid reload overhead
6. **Defensive Initialization**: `_ensure_onboarding_defaults()` makes configs forward-compatible

## Knowledge Gaps

- `ModelsRegistry` is defined but not actively used in the main codebase (future feature)
- `format_token_count()` in token_counter.py has no callers
- Duplicate `get_tool_description()` exists in both `tool_descriptions.py` and `agent_helpers.py`

## References

- `/root/tunacode/src/tunacode/utils/file_utils.py` - DotDict, capture_stdout
- `/root/tunacode/src/tunacode/utils/text_utils.py` - @file expansion logic
- `/root/tunacode/src/tunacode/utils/json_utils.py` - Concatenated JSON handling
- `/root/tunacode/src/tunacode/utils/diff_utils.py` - Rich diff rendering
- `/root/tunacode/src/tunacode/utils/api_key_validation.py` - Provider mapping
- `/root/tunacode/src/tunacode/utils/models_registry.py` - models.dev integration
- `/root/tunacode/src/tunacode/utils/completion_utils.py` - Path autocomplete
- `/root/tunacode/src/tunacode/utils/user_configuration.py` - Fingerprint caching
- `/root/tunacode/src/tunacode/utils/config_comparator.py` - Recursive diff analysis
- `/root/tunacode/src/tunacode/utils/system.py` - Gitignore pattern matching
- `/root/tunacode/src/tunacode/utils/message_utils.py` - Polymorphic extraction
- `/root/tunacode/src/tunacode/utils/token_counter.py` - Tiktoken integration
- `/root/tunacode/src/tunacode/utils/tool_descriptions.py` - UI descriptions
- `/root/tunacode/src/tunacode/utils/retry.py` - Exponential backoff
- `/root/tunacode/src/tunacode/utils/security.py` - Injection prevention
- `/root/tunacode/src/tunacode/utils/import_cache.py` - Lazy imports
