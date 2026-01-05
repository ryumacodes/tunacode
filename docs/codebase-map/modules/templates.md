---
title: Templates Module
path: src/tunacode/templates
type: directory
depth: 1
description: Template management and loading system
exports: [Template, TemplateLoader, load_template]
seams: [M]
---

# Templates Module

## Purpose
Manages agent templates including metadata, allowed tools, and template-specific constraints.

## Key Components

### loader.py
**TemplateLoader Class**
Template loading and management:
- **load_template()** - Load template by name
- **list_templates()** - Get available templates
- **validate_template()** - Validate template structure
- **get_template_metadata()** - Get template info

### __init__.py
Template definitions and exports:
- Default template
- Template metadata
- Template validation

## Template Structure

**Template Definition:**
```python
{
  "name": str,
  "description": str,
  "system_prompt_override": str | None,
  "allowed_tools": list[str] | None,
  "max_iterations": int | None,
  "yolo_mode": bool,
  "metadata": dict
}
```

## Template Features

### System Prompt Override
Custom system prompt sections:
- Replace default agent role
- Add template-specific rules
- Customize tool usage guidelines

### Allowed Tools
Restrict tool access:
- Whitelist specific tools
- Enforce template boundaries
- Prevent unauthorized actions

### Custom Parameters
Template-specific settings:
- **max_iterations** - Adjust loop limit
- **yolo_mode** - Override authorization
- **timeout** - Custom timeouts

## Template Locations

```
~/.config/tunacode/templates/
├── default.json
├── researcher.json
├── coder.json
└── custom.json
```

## Template Examples

**Default Template:**
- All tools available
- Standard system prompt
- User confirmation required

**Researcher Template:**
- Read-only tools only (glob, grep, read_file)
- Research-focused system prompt
- No confirmation for safe tools

**Coder Template:**
- Full tool access
- Code-focused prompts
- Stricter validation

## Integration Points

- **core/agents/** - Template loading for agent creation
- **tools/authorization/** - Allowed tools enforcement
- **configuration/** - Template selection in user config
- **ui/screens/** - Template selection UI

## Seams (M)

**Modification Points:**
- Add new templates
- Extend template schema
- Customize template loading logic
- Add template validation rules

**Extension Points:**
- Create custom template types
- Implement template inheritance
- Add template composition
- Create template marketplace
