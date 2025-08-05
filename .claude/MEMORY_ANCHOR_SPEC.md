# Memory Anchor Specification

## Purpose

Memory anchors provide persistent reference points in code for Claude and other LLMs to navigate and understand the codebase efficiently, even as the code evolves.

## Format

```python
CLAUDE_ANCHOR[anchor-key]: Description of this code section
```

## Placement Rules

1. **In Docstrings**: Place anchors within module, class, or function docstrings
2. **Single Line**: Keep anchor and description on one line for easy parsing
3. **Unique Keys**: Each anchor key must be unique across the codebase

## Naming Conventions

- **Modules**: `module-name` (e.g., `main-agent-module`)
- **Classes**: `class-name` or `feature-class` (e.g., `state-manager`)
- **Functions**: `function-purpose` (e.g., `process-request-entry`)
- **Critical Sections**: `feature-handler` (e.g., `error-recovery-handler`)

## Examples

### Module Level
```python
"""Module for handling user authentication.

CLAUDE_ANCHOR[auth-module]: Core authentication and session management
"""
```

### Class Level
```python
class RequestProcessor:
    """CLAUDE_ANCHOR[request-processor]: Main request handling pipeline"""
```

### Function Level
```python
async def handle_error(error: Exception):
    """Handle errors gracefully.

    CLAUDE_ANCHOR[error-handler]: Central error handling and recovery
    """
```

## Tool Compatibility

- **Mypy**: Anchors in docstrings are ignored by type checkers
- **Linters**: No impact on code quality tools
- **IDEs**: Appears as regular documentation
- **Version Control**: Travels with code through merges and refactors

## Maintenance

1. Add anchors when creating critical new components
2. Update `anchors.json` with new anchor mappings
3. Mark old anchors as "tombstone" when removing code
4. Never reuse anchor keys

## Benefits

- **Persistent Navigation**: Find code sections even after refactoring
- **Context Preservation**: Maintain understanding across sessions
- **Cross-Reference**: Link QA entries and documentation to specific code
- **LLM-Friendly**: Optimized for machine parsing and understanding
