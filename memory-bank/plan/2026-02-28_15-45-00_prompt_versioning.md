---
title: "Prompt Versioning – Plan"
phase: Plan
date: "2026-02-28T15:45:00"
owner: "claude"
parent_research: "memory-bank/research/2026-02-28_15-17-48_system_prompt_architecture.md"
git_commit_at_plan: "56a05fc7"
tags: [plan, prompt-versioning, coding]
---

## Goal

Add explicit version tracking for system prompt and tool prompt changes in tunacode

## Scope & Assumptions

### In Scope

- Version tracking for `src/tunacode/prompts/system_prompt.md`
- Version tracking for XML prompts in `src/tunacode/tools/prompts/`
- Version tracking for dynamic context (AGENTS.md/guide_file)
- Version metadata storage and retrieval
- Version display in logs/debug output
- Simple version comparison utilities

### Out of Scope

- UI-based prompt editing
- Remote prompt storage/syncing
- Automated prompt testing/validation

### Assumptions

- File content hashing (SHA-256) is sufficient for version computation
- Versions are computed at runtime when prompts are loaded
- Version metadata stored locally (no external service dependency)
- Existing mtime-aware cache pattern will be extended for versioning

## Deliverables

- `src/tunacode/prompts/versioning.py` - Version computation and storage module
- `src/tunacode/types/canonical.py` - `PromptVersion` dataclass
- `src/tunacode/infrastructure/cache/caches/prompt_version_cache.py` - Version cache
- Modified `agent_config.py` - Integrate versioning into `load_system_prompt()` and `load_tunacode_context()`
- Modified tool decorators - Capture tool prompt versions
- Version logging in agent execution flow
- Developer documentation in `docs/modules/prompts/versioning.md`

## Readiness

### Preconditions

- Existing codebase at commit 56a05fc7
- `src/tunacode/prompts/system_prompt.md` exists
- Tool XML prompts exist in `src/tunacode/tools/prompts/`
- Existing cache infrastructure in `src/tunacode/infrastructure/cache/`

### External Dependencies

- None beyond existing stack (Python 3.11+, standard library)

### Data Schema

```python
@dataclass(frozen=True)
class PromptVersion:
    """Immutable version identifier for a prompt."""
    source_path: str  # Path to prompt file
    content_hash: str  # SHA-256 of content
    mtime: float  # File modification time
    computed_at: float  # When version was computed
    length: int  # Character count for size tracking

@dataclass(frozen=True)
class AgentPromptVersions:
    """Combined version report for all prompts used by an agent."""
    system_prompt: PromptVersion | None
    tunacode_context: PromptVersion | None
    tool_prompts: dict[str, PromptVersion]  # tool_name -> version
    fingerprint: str  # Combined hash of all versions
    computed_at: float
```

## Milestones

### M1: Core Versioning Data Structures

- Define `PromptVersion` and `AgentPromptVersions` types
- Create version computation function from file content
- Add comprehensive type hints and frozen dataclasses

### M2: Version Computation Module

- Implement `compute_prompt_version()` function
- Implement `compute_agent_prompt_versions()` aggregator
- Add version comparison utilities
- Unit tests for version computation

### M3: Cache Integration

- Extend existing mtime-aware cache pattern for versions
- Create `PromptVersionCache` class
- Integrate version caching into prompt loading flow

### M4: Agent Integration

- Modify `load_system_prompt()` to capture version
- Modify `load_tunacode_context()` to capture version
- Modify tool loading to capture XML prompt versions
- Attach version metadata to agent instances

### M5: Observability

- Log prompt versions at agent creation
- Add version to debug/verbose output
- Create utility for displaying current versions

## Work Breakdown (Tasks)

| ID  | Task                                                    | Owner  | Estimate | Dependencies | Milestone | Acceptance Test                                                                                      | Files Touched                                                      |
| --- | ------------------------------------------------------- | ------ | -------- | ------------ | --------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| T1  | Define PromptVersion dataclass in canonical.py          | claude | 15min    | -            | M1        | `PromptVersion("path", "hash", 1.0, 2.0, 100)` creates valid instance                                | `src/tunacode/types/canonical.py`                                  |
| T2  | Define AgentPromptVersions dataclass in canonical.py    | claude | 10min    | T1           | M1        | `AgentPromptVersions(...)` creates valid instance with fingerprint                                   | `src/tunacode/types/canonical.py`                                  |
| T3  | Create compute_prompt_version() function                | claude | 30min    | T1, T2       | M2        | compute_prompt_version("path/to/file.md") returns PromptVersion with valid SHA256                    | `src/tunacode/prompts/versioning.py`                               |
| T4  | Create compute_agent_prompt_versions() aggregator       | claude | 30min    | T3           | M2        | compute_agent_prompt_versions(system_path, context_path, tool_paths) returns AgentPromptVersions     | `src/tunacode/prompts/versioning.py`                               |
| T5  | Write unit tests for version computation                | claude | 20min    | T3, T4       | M2        | Test passes for identical files producing same version, different files producing different versions | `tests/unit/prompts/test_versioning.py`                            |
| T6  | Create PromptVersionCache class                         | claude | 30min    | T3           | M3        | PromptVersionCache.get(path) returns cached PromptVersion if file unchanged                          | `src/tunacode/infrastructure/cache/caches/prompt_version_cache.py` |
| T7  | Modify load_system_prompt() to capture version          | claude | 20min    | T3, T6       | M4        | load_system_prompt() returns (prompt_content, PromptVersion) tuple                                   | `src/tunacode/core/agents/agent_components/agent_config.py`        |
| T8  | Modify load_tunacode_context() to capture version       | claude | 20min    | T3, T6       | M4        | load_tunacode_context() returns (context_content, PromptVersion) tuple                               | `src/tunacode/core/agents/agent_components/agent_config.py`        |
| T9  | Capture tool XML prompt versions in to_tinyagent_tool() | claude | 30min    | T3           | M4        | to_tinyagent_tool() captures PromptVersion for XML-loaded tools                                      | `src/tunacode/tools/decorators.py`                                 |
| T10 | Attach versions to agent instances                      | claude | 30min    | T7, T8, T9   | M4        | Agent instances have prompt_versions attribute containing AgentPromptVersions                        | `src/tunacode/core/agents/agent_components/agent_config.py`        |
| T11 | Add version logging at agent creation                   | claude | 15min    | T10          | M5        | Agent creation logs include "System prompt version: {hash[:8]}..."                                   | `src/tunacode/core/agents/agent_components/agent_config.py`        |
| T12 | Create version display CLI/debug utility                | claude | 20min    | T10          | M5        | `tk prompt-versions` or similar displays current prompt versions                                     | `src/tunacode/cli/` (new file)                                     |
| T13 | Write developer documentation                           | claude | 30min    | T10          | M5        | docs/modules/prompts/versioning.md exists and explains the system                                    | `docs/modules/prompts/versioning.md`                               |

## Risks & Mitigations

| Risk                                           | Impact                                   | Mitigation                                                               |
| ---------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------ |
| Hash computation adds latency to agent startup | Low (SHA-256 is fast, caching mitigates) | Use mtime-based cache invalidation, only hash when changed               |
| Version cache desync with actual files         | Medium                                   | Invalidate cache on mtime change, not time-based                         |
| Large AGENTS.md causes slow hashing            | Low                                      | Hash only on first load, cached until mtime change                       |
| Version storage grows unbounded                | Low                                      | Versions are immutable and small (path + hash), can be kept indefinitely |

## Test Strategy

- **T5**: Single unit test covering hash consistency and difference detection
- No integration test required for M1-M3 (pure functions with clear inputs/outputs)
- M4-M5 verification through manual testing with verbose logging

## References

### Research Sections

- "Knowledge Gaps" section identifies "Prompt versioning" as missing
- "Three-Level Caching" pattern to be extended
- "Data Flow" section shows integration points

### Code References

- `src/tunacode/core/agents/agent_components/agent_config.py:144-174` - Current prompt loading
- `src/tunacode/infrastructure/cache/caches/tunacode_context.py` - Existing mtime-aware cache pattern
- `src/tunacode/tools/cache_accessors/xml_prompts_cache.py` - XML prompt caching
- `src/tunacode/tools/xml_helper.py:13-46` - XML prompt loading

### Implementation Pattern

Follow existing cache pattern:

```python
# Existing pattern from tunacode_context.py
def _get_cached(self, path: str) -> str | None:
    mtime = os.path.getmtime(path)
    cached_mtime = self._mtime_cache.get(path)
    if cached_mtime == mtime:
        return self._content_cache.get(path)
    return None
```

## Final Gate

**Output Summary:**

- Plan path: `memory-bank/plan/2026-02-28_15-45-00_prompt_versioning.md`
- Milestones: 5 (M1: Data structures, M2: Computation, M3: Cache, M4: Integration, M5: Observability)
- Tasks: 13 ready for coding
- Estimated effort: ~5 hours

**Next Command:**

```bash
/execute "memory-bank/plan/2026-02-28_15-45-00_prompt_versioning.md"
```

Or to start fresh with tickets:

```bash
/context-engineer:plan-with-tickets "memory-bank/research/2026-02-28_15-17-48_system_prompt_architecture.md"
```
