---
title: Core Prompting Engine
path: src/tunacode/core/prompting
type: directory
depth: 1
description: System prompt composition from modular sections
exports: [PromptingEngine, SectionLoader, compose_prompt, SystemPromptSection]
seams: [M, D]
---

# Core Prompting Engine

## Purpose
Composes modular system prompts from sections, templates, and dynamic placeholders for AI agents.

## Key Components

### Prompting Engine (prompting_engine.py)

**PromptingEngine Class**
- Loads and caches prompt sections from files
- Resolves dynamic placeholders ({{CWD}}, {{OS}}, {{DATE}})
- Applies model-specific template overrides
- Composes final system prompt from sections

**Dynamic Placeholders:**
- `{{CWD}}` - Current working directory
- `{{OS}}` - Operating system name
- `{{DATE}}` - Current date
- `{{AGENTS_MD_CONTENT}}` - Project-specific AGENTS.md content

**Templates:**
- **MAIN_TEMPLATE** - Standard agent prompt structure
- **RESEARCH_TEMPLATE** - Research agent prompt structure
- **TEMPLATE_OVERRIDES** - Model-specific variations

### Section Loader (loader.py)

**SectionLoader Class**
- Reads markdown section files from prompts/ directory
- Caches loaded sections for performance
- Provides get_section() method for section retrieval

### Sections (sections.py)

**SystemPromptSection Enum**
Defines all prompt section types:
- **AGENT_ROLE** - Core agent identity and purpose
- **CRITICAL_RULES** - Mandatory behavior constraints
- **TOOL_USE** - Tool usage guidelines
- **CODE_STYLE** - Code quality standards
- **WORKFLOW** - Step-by-step process rules
- **OUTPUT_FORMAT** - Response format requirements

### Templates (templates.py)

Template definitions and constants for prompt composition.

## Section Files Location

```
src/tunacode/prompts/sections/
├── agent_role.md
├── critical_rules.md
├── tool_use.md
├── code_style.md
├── workflow.md
└── output_format.md
```

## Prompt Composition Flow

```
1. Load sections from files (SectionLoader)
2. Resolve dynamic placeholders ({{CWD}}, {{OS}}, etc.)
3. Select template (MAIN or RESEARCH)
4. Apply model-specific overrides
5. Compose final system prompt
```

## Integration Points

- **core/agents/agent_config.py** - Loads prompts for agent creation
- **core/agents/prompts.py** - Intervention prompt templates
- **configuration/** - Model-specific settings
- **AGENTS.md** - Project-specific context injection

## Seams (M, D)

**Modification Points:**
- Add new prompt section types
- Customize placeholder resolution logic
- Extend template variations
- Add model-specific prompt overrides

**Extension Points:**
- Create custom section loaders
- Implement dynamic prompt generators
- Add prompt validation/analysis
- Support prompt versioning
