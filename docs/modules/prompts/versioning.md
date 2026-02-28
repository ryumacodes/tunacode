# Prompt Versioning

## Overview

The prompt versioning system provides explicit version tracking for system prompts and tool prompts in tunacode. This enables:

- Detection of prompt changes between agent instances
- Cache invalidation when prompts are modified
- Debugging and observability for prompt-related issues
- Reproducibility by tracking which prompt versions were used

## Architecture

### Core Components

- **`src/tunacode/types/canonical.py`**: `PromptVersion` and `AgentPromptVersions` dataclasses
- **`src/tunacode/prompts/versioning.py`**: Version computation and caching
- **`src/tunacode/infrastructure/cache/caches/prompt_version_cache.py`**: mtime-aware version cache
- **`src/tunacode/prompts/version_display.py`**: Display utilities

### Data Structures

```python
@dataclass(frozen=True, slots=True)
class PromptVersion:
    """Immutable version identifier for a prompt."""
    source_path: str      # Path to prompt file
    content_hash: str     # SHA-256 of content
    mtime: float          # File modification time
    computed_at: float    # When version was computed
    length: int           # Character count

@dataclass(frozen=True, slots=True)
class AgentPromptVersions:
    """Combined version report for all prompts used by an agent."""
    system_prompt: PromptVersion | None
    tunacode_context: PromptVersion | None
    tool_prompts: dict[str, PromptVersion]  # tool_name -> version
    fingerprint: str      # Combined hash of all versions
    computed_at: float
```

## Usage

### Computing Prompt Versions

```python
from tunacode.prompts.versioning import get_or_compute_prompt_version

# Get or compute version (with caching)
version = get_or_compute_prompt_version("prompts/system_prompt.md")
print(f"Hash: {version.content_hash[:16]}...")
```

### Agent Integration

When an agent is created, prompt versions are automatically captured:

```python
from tunacode.core.agents.agent_components.agent_config import get_or_create_agent

agent = get_or_create_agent(model="gpt-4", state_manager=...)

# Access prompt versions
versions = agent.prompt_versions
print(f"Fingerprint: {versions.fingerprint}")
```

### Displaying Versions

```python
from tunacode.prompts.version_display import print_prompt_versions

# Print current prompt versions to stdout
print_prompt_versions()
```

## Caching

Prompt versions are cached using an mtime-aware strategy:

- Cache key: resolved file path
- Cache invalidation: file mtime change
- Cache entry: `PromptVersion` object

The cache prevents recomputing SHA-256 hashes on every agent creation.

## Version Computation

1. **File content** is read as UTF-8 text
2. **SHA-256 hash** is computed from the content
3. **Modification time** is retrieved from the filesystem
4. **Length** is the character count of the content

For `AgentPromptVersions`, the fingerprint is computed by concatenating all individual hashes with a delimiter:

```
"system:{hash}|context:{hash}|bash:{hash}|read_file:{hash}|..."
```

## Integration Points

### System Prompt Loading

```python
# src/tunacode/core/agents/agent_components/agent_config.py
def load_system_prompt(base_path: Path, model: str | None = None) -> tuple[str, PromptVersion | None]:
    """Load the system prompt with version tracking."""
    content = prompt_file.read_text(encoding="utf-8")
    version = get_or_compute_prompt_version(prompt_file)
    return content, version
```

### Tool Prompt Versioning

```python
# src/tunacode/tools/decorators.py
def to_tinyagent_tool(func, *, name=None, label=None) -> AgentTool:
    """Convert tool function with prompt version capture."""
    xml_path = get_xml_prompt_path(tool_name)
    if xml_path is not None:
        prompt_version = get_or_compute_prompt_version(xml_path)
    agent_tool.prompt_version = prompt_version
    return agent_tool
```

## Observability

### Agent Creation Logging

When an agent is created, the following is logged:

```
Agent created: gpt-4, system_prompt=a1b2c3d4e5f6..., context=b2c3d4e5f6a7..., fingerprint=c3d4e5f6a7b8...
```

### Debugging Prompt Issues

If you suspect a prompt-related issue:

1. Check the agent creation logs for version hashes
2. Use `print_prompt_versions()` to inspect current versions
3. Compare fingerprints between working and broken sessions

## File Locations

| Component | Path |
|-----------|------|
| System prompt | `src/tunacode/prompts/system_prompt.md` |
| Tool prompts | `src/tunacode/tools/prompts/{tool}_prompt.xml` |
| Context file | `AGENTS.md` (configurable via `guide_file` setting) |

## Implementation Notes

- **Immutability**: `PromptVersion` and `AgentPromptVersions` are frozen dataclasses
- **Cache strategy**: mtime-based (invalidates on file modification)
- **Hash algorithm**: SHA-256 (cryptographic, collision-resistant)
- **Performance**: Hashing is fast; caching makes it negligible
- **Thread safety**: Read-only operations; cache is internally synchronized

## Future Enhancements

Potential improvements (out of scope for initial implementation):

- UI-based prompt editing with version history
- Remote prompt storage/syncing
- Automated prompt testing/validation
- Prompt rollback/undo functionality
