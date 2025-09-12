# Research – Model Selection Configuration Update Issue
**Date:** 2025-09-12 15:06:58
**Owner:** Claude Code Research Agent
**Phase:** Research

## Goal
Investigate why the recent model selection update works but doesn't change the config file. Research the implementation to understand the gap between model selection functionality and configuration file persistence.

## Additional Search
- `grep -ri "model.*config" .claude/`
- `grep -ri "default.*model" .claude/`

## Findings
- **Recent Model Update**: PR #91 introduced models.dev integration with multi-source routing (613+ models from 15+ providers)
- **Model Command Implementation**: `/model` command in `src/tunacode/cli/commands/implementations/model.py`
- **Config File Location**: `~/.config/tunacode.json`
- **Core Issue**: Model selection only updates session state, requires explicit "default" keyword to persist to config file

## Relevant Files & Why They Matter
- **`src/tunacode/cli/commands/implementations/model.py`** → Main model command interface where the persistence gap exists
- **`src/tunacode/utils/user_configuration.py`** → Contains `set_default_model()` function that saves to config file
- **`src/tunacode/core/setup/config_setup.py`** → Configuration loading and validation logic
- **`src/tunacode/core/state.py`** → Session state management with `current_model` field
- **`src/tunacode/utils/models_registry.py`** → models.dev integration with caching and multi-source routing

## Key Patterns / Solutions Found

### 1. Model Selection Flow Gap
**Pattern**: Session-only updates vs config persistence
- `/model provider:model` → Updates `session.current_model` only (line 160 in model.py)
- `/model provider:model default` → Calls `set_default_model()` and saves to config (lines 163-170)
- **Issue**: Users don't know about the "default" keyword requirement

### 2. Configuration Save Logic
**Pattern**: Explicit save required
- `set_default_model()` in `user_configuration.py:89-97` handles config persistence
- `save_config()` function writes JSON to `~/.config/tunacode.json`
- **Solution**: Function works correctly but isn't called for regular model changes

### 3. Fast Path Validation Bypass
**Pattern**: Config fingerprinting can prevent updates
- Lines 61-72 in `config_setup.py` use fingerprinting to skip validation
- `_config_valid` flag must be true for fast path to work
- **Issue**: Failed validation can prevent config saves entirely

### 4. Multi-source Routing Without Persistence
**Pattern**: Advanced model discovery without preference storage
- Models registry provides excellent routing alternatives (lines 485-564)
- User can select from multiple providers for same model
- **Gap**: No mechanism to persist provider routing preferences

## Knowledge Gaps
- Need to verify current behavior: does `/model <model>` change config file?
- What specific failure modes occur when config file isn't updated?
- Are there file permission or API key validation issues blocking saves?
- Should model changes automatically persist or remain session-only by design?

## References
- **PR #91**: `git show 43e8881` - models.dev integration merge
- **Model Command**: `src/tunacode/cli/commands/implementations/model.py:162-170`
- **Config Save Logic**: `src/tunacode/utils/user_configuration.py:89-97`
- **Recent Crash Analysis**: `memory-bank/research/2025-09-12_14-54-43_model_configuration_crash_analysis.md`
- **GitHub Repo**: https://github.com/alchemiststudiosDOTai/tunacode
