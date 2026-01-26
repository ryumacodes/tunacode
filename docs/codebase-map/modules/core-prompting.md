---
title: Core Prompting Engine
path: src/tunacode/core/prompting
type: directory
depth: 1
description: Dynamic placeholder resolution for system prompts
exports: [resolve_prompt]
seams: [M, D]
---

# Core Prompting Engine

## Purpose
Resolves dynamic placeholders in system prompt strings for AI agents.

## Key Components

### Prompting Engine (prompting_engine.py)

**Dynamic Placeholders:**
- `{{CWD}}` - Current working directory
- `{{OS}}` - Operating system name
- `{{DATE}}` - Current date

**resolve_prompt Function**
- Takes a prompt string with placeholders
- Replaces placeholders with actual values
- Returns resolved prompt ready for use

## Guide Files

```
<cwd>/AGENTS.md      # Project-specific context injection
```

Context injection via `{{USER_INSTRUCTIONS}}` placeholder:
- Loads from `settings.guide_file` (defaults to AGENTS.md)
- Injected into system prompt at runtime
- Provides project-specific context to the agent

## Prompt Loading Flow

```
1. Load system_prompt.md from src/tunacode/prompts/
2. Resolve dynamic placeholders ({{CWD}}, {{OS}}, {{DATE}})
3. Inject AGENTS.md content if available
4. Return final system prompt
```

## Integration Points

- **core/agents/agent_config.py** - Loads system_prompt.md and resolves placeholders
- **prompts/system_prompt.md** - Single unified agent prompt file (11 sections)
- **AGENTS.md** - Project-specific context injection

## Seams (M, D)

**Modification Points:**
- Add new dynamic placeholder types
- Customize placeholder resolution logic
- Extend placeholder syntax

**Extension Points:**
- Create custom placeholder resolvers
- Implement prompt validation/analysis
- Support conditional placeholders
