---
title: Prompts Module
path: src/tunacode/prompts
type: directory
depth: 1
description: Modular prompt templates and sections
exports: [agent_role.md, critical_rules.md, tool_use.md]
seams: [M]
---

# Prompts Module

## Purpose
Stores modular prompt sections and templates used to compose system prompts for AI agents.

## Directory Structure

```
src/tunacode/prompts/
├── sections/
│   ├── agent_role.md
│   ├── critical_rules.md
│   ├── tool_use.md
│   ├── code_style.md
│   ├── workflow.md
│   └── output_format.md
└── templates/
    ├── main.md
    └── research.md
```

## Prompt Sections

### agent_role.md
Defines the agent's core identity and purpose:
- Agent role and responsibilities
- Primary objectives
- Expected behavior
- Scope of capabilities

### critical_rules.md
Mandatory behavior constraints:
- Safety requirements
- Error handling rules
- Tool usage constraints
- User interaction guidelines

### tool_use.md
Tool usage guidelines:
- How to select appropriate tools
- Tool parameter requirements
- Tool result interpretation
- Tool combination strategies

### code_style.md
Code quality standards:
- Naming conventions
- Code organization
- Comment requirements
- Type safety rules

### workflow.md
Step-by-step process rules:
- Task decomposition
- Iteration strategy
- Completion criteria
- Progress tracking

### output_format.md
Response format requirements:
- Structured output guidelines
- Explanation expectations
- Result presentation
- Status reporting

## Prompt Templates

### main.md
Standard agent prompt template:
- Combines all sections
- Standard ordering
- Default placeholders

### research.md
Research agent prompt template:
- Focused on exploration
- Read-only tool emphasis
- Structured reporting format

## Section Format

Each section follows this structure:
```markdown
# Section Title

Brief description of the section's purpose.

## Subsection 1

Detailed guidelines...

## Subsection 2

More details...
```

## Placeholders

Dynamic placeholders resolved at runtime:
- `{{CWD}}` - Current working directory
- `{{OS}}` - Operating system
- `{{DATE}}` - Current date
- `{{AGENTS_MD_CONTENT}}` - Project-specific context

## Loading Process

```
1. SectionLoader reads section files
2. PromptingEngine resolves placeholders
3. compose_prompt() assembles sections
4. Template overrides applied (if any)
5. Final system prompt generated
```

## Integration Points

- **core/prompting/** - Section loading and composition
- **core/agents/agent_config.py** - Prompt injection into agents
- **AGENTS.md** - Project-specific context injection

## Customization

Users can customize prompts by:
1. Modifying section files in `~/.config/tunacode/prompts/`
2. Adding custom sections
3. Creating custom templates
4. Overriding in project-specific AGENTS.md

## Seams (M)

**Modification Points:**
- Edit section files directly
- Add new prompt sections
- Modify template structure
- Customize placeholder resolution

**Best Practices:**
- Keep sections focused and modular
- Use clear, concise language
- Provide examples
- Maintain consistency across sections
