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

The `anchors.json` file maps these in-file anchors with their locations and descriptions.

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

- `anchors.json` - Maps in-file CLAUDE_ANCHOR tags with locations
- `metadata/components.yml` - Component dependency graph
- `metadata/hotspots.txt` - High-churn files requiring attention
- `delta/YYYY-MM-DD-baseline.yml` - Daily baseline snapshots
- `NEXT_PR_RULES.md` - Maintenance guidelines for contributors

## Usage

Files are designed for machine parsing. Updates should preserve existing keys and merge new data idempotently.

### Adding New Anchors

When adding critical code sections:
1. Add `CLAUDE_ANCHOR[descriptive-key]: Brief description` comment
2. Update `anchors.json` with the new anchor reference
3. Use consistent naming: `module-name`, `feature-handler`, `critical-function`
