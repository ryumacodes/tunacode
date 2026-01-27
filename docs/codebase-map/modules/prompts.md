---
title: Prompts Module
path: src/tunacode/prompts
type: directory
depth: 1
description: Unified agent system prompt file
exports: [system_prompt.md]
seams: [M]
---

# Prompts Module

## Purpose
Stores the unified system prompt used by agents. Tool prompts remain separate and unchanged.

## Directory Structure

```
src/tunacode/prompts/
└── system_prompt.md
```

## system_prompt.md
Single source of truth for the agent system prompt:
- Contains all prompt sections in a fixed order
- Includes `{{USER_INSTRUCTIONS}}` placeholder for injected context
- Uses dynamic placeholders resolved at runtime ({{CWD}}, {{OS}}, {{DATE}})

## Loading Process

```
1. Read system_prompt.md
2. Resolve dynamic placeholders ({{CWD}}, {{OS}}, {{DATE}})
3. Inject AGENTS.md content via {{USER_INSTRUCTIONS}}
4. Return final system prompt
```

## Integration Points

- **core/agents/agent_config.py** - Reads system_prompt.md and resolves placeholders
- **core/prompting/prompting_engine.py** - Placeholder resolution
- **AGENTS.md** - Project-specific context injection

## Seams (M)

**Modification Points:**
- Edit system_prompt.md content
- Adjust placeholder resolution behavior

**Best Practices:**
- Keep sections ordered and consistent
- Avoid duplicating tool prompt content
