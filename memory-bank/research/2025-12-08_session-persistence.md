# Research - Session Persistence (OpenCode-style)

**Date:** 2025-12-08
**Owner:** agent
**Phase:** Research

## Goal

Implement persistent session storage so users can resume conversations across app restarts, inspired by OpenCode's file-based JSON approach.

## Current State

| Aspect | Status |
|--------|--------|
| Session ID | UUID generated per session (`state.py:46`) |
| Messages | In-memory only, lost on restart |
| Session directories | Created at `~/.tunacode/sessions/{id}/` but cleaned up on exit |
| User config | Persisted at `~/.config/tunacode.json` |
| XDG support | None - hardcoded paths |

## OpenCode Approach (Inspiration)

```
~/.local/share/opencode/storage/session/[projectID]/[sessionID].json
```

Key patterns:
- **Project ID**: Hash of git repo root path
- **File locking**: OS-level locks prevent corruption
- **XDG paths**: Platform-appropriate directories
- **Independence**: Sessions persist regardless of auth/logout

## Findings

### Files to Modify

| File | Change |
|------|--------|
| `src/tunacode/core/state.py:30-90` | Add `project_id`, `created_at`, `last_modified` fields to `SessionState` |
| `src/tunacode/core/state.py:105` | Add `save_session()`, `load_session()` methods to `StateManager` |
| `src/tunacode/utils/system/paths.py` | Add `get_project_id()`, `get_session_storage_dir()` |
| `src/tunacode/ui/app.py:216-217` | Save session on exit |
| `src/tunacode/ui/commands/__init__.py:184` | Add `/sessions` command |

### SessionState Fields to Serialize

**Essential (persist):**
- `messages` - conversation history
- `current_model` - active model
- `session_id` - unique identifier
- `total_tokens` - token count
- `session_total_usage` - cost tracking
- `tool_ignore` - permission preferences
- `yolo` - auto-approve setting
- `react_scratchpad` - tool timeline
- NEW: `project_id`, `created_at`, `last_modified`, `working_directory`

**Skip (runtime-only):**
- `user_config` - loaded separately
- `agents` - runtime instances
- `spinner`, `streaming_panel` - UI widgets
- `operation_cancelled`, `is_streaming_active` - transient flags

### Project ID Strategy

```python
def get_project_id() -> str:
    """Hash git repo root or cwd for project identification."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            return hashlib.sha256(result.stdout.strip().encode()).hexdigest()[:16]
    except Exception:
        pass
    return hashlib.sha256(os.getcwd().encode()).hexdigest()[:16]
```

### Storage Path (XDG-compliant)

```python
def get_session_storage_dir() -> Path:
    xdg_data = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))
    return Path(xdg_data) / 'tunacode' / 'sessions'
```

### Message Serialization Challenge

Messages are pydantic-ai `ModelRequest`/`ModelResponse` objects. Use:
```python
msg.model_dump(mode='json')  # Pydantic v2
```

## Key Patterns / Solutions Found

- `get_model_pricing()` in `pricing.py` - pattern for registry lookups
- `save_config()` in `user_configuration.py` - pattern for JSON persistence with error handling
- `cleanup_session()` in `paths.py` - currently deletes sessions, needs inversion

## Implementation Checklist

### Core Infrastructure
- [ ] Add `get_project_id()` to `paths.py`
- [ ] Add XDG session storage path
- [ ] Add serialization fields to `SessionState`
- [ ] Implement `save_session()` / `load_session()` in `StateManager`
- [ ] Add file locking utility

### UI Integration
- [ ] Add `/sessions` command (list/load/delete)
- [ ] Create `SessionResumeScreen` for startup
- [ ] Add session status to status bar
- [ ] Auto-save on exit
- [ ] Periodic auto-save worker

### Save Triggers
1. After message processing (`app.py:269`)
2. After compaction
3. On `/clear` command
4. On exit
5. Periodic background (every 60s)

## Knowledge Gaps

- Need to test pydantic-ai message serialization/deserialization roundtrip
- Determine session retention policy (how long to keep old sessions?)
- Consider session size limits

## References

- `src/tunacode/core/state.py` - SessionState and StateManager
- `src/tunacode/utils/config/user_configuration.py` - Pattern for JSON persistence
- `src/tunacode/utils/system/paths.py` - Path utilities
- `src/tunacode/ui/app.py` - Application lifecycle hooks
- OpenCode source: `storage/storage.ts`, `session/index.ts`
