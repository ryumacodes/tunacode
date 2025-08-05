# .claude Directory Structure

This directory contains optimized metadata for Claude/LLM interaction with the TunaCode repository.

## Memory Anchors

Memory anchors are embedded directly in source files using the format:
```python
CLAUDE_ANCHOR[anchor-key]: Description of this code section
```

These anchors provide:
- **Persistent references** across code changes
- **Semantic context** for important code sections
- **Quick navigation** to critical implementation points
- **LLM optimization** for improved code understanding and navigation
- **Cross-session memory** to maintain context between different sessions

The `anchors.json` file maps these in-file anchors with their locations and descriptions. Current anchors include:
- `main-agent-module`: Core agent with parallel tool execution
- `grep-module`: Fast parallel file search with 3-second deadline
- `parallel-grep-class`: Main grep implementation with timeout handling
- `state-manager`: Central application state management
- `request-processor`: Main request handling pipeline

## Structure

- **agents/** - Agent-specific configurations and prompts
- **commands/** - Command templates and patterns
- **code_index/** - Semantic code relationships and call graphs
- **debug_history/** - Historical debugging sessions and solutions
- **delta/** - Version-to-version change summaries
- **metadata/** - Component metadata and hotspots
- **patterns/** - Code patterns and implementation templates
- **qa/** - Question-answer pairs from resolved issues
- **scratchpad/** - Temporary working notes

## Key Files

- `anchors.json` - Maps in-file CLAUDE_ANCHOR tags with locations and descriptions
- `MEMORY_ANCHOR_SPEC.md` - Specification for memory anchor format and usage
- `NEXT_PR_RULES.md` - Maintenance guidelines for contributors
- `settings.local.json` - Local Claude configuration settings
- `agents/tech-docs-maintainer.md` - Documentation maintenance agent definition

## Recent Updates

This directory now includes:

- **Memory Anchor Specification** - Formal specification for in-file anchor usage
- **Agent Definitions** - Specialized agents for different development tasks
- **Enhanced Documentation** - Improved structure for better LLM navigation
- **Tool Integration** - Better integration with TunaCode's parallel tool execution system

## Usage

Files are designed for machine parsing. Updates should preserve existing keys and merge new data idempotently.

### Adding New Anchors

When adding critical code sections:
1. Add `CLAUDE_ANCHOR[descriptive-key]: Brief description` comment
2. Update `anchors.json` with the new anchor reference
3. Use consistent naming: `module-name`, `feature-handler`, `critical-function`
