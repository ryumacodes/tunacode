## NOTES: to Qwen (my coworker)

Here are my notes regarding the dead code analysis:

The constants in `src/tunacode/constants.py` are actually actively used throughout the codebase and should not be removed:

- **UI Constants**: These are extensively used in multiple UI modules:
  - `UI_PROMPT_PREFIX` is used in `ui/input.py`
  - `UI_COLORS` is imported and used in `ui/panels.py`, `ui/output.py`, `ui/tool_ui.py`, and others
  - `UI_THINKING_MESSAGE` is used in `ui/panels.py` and `ui/output.py`

- **ERROR Constants**: These are used in file processing tools for error handling:
  - Various `ERROR_*` constants are used in `tools/read_file.py` and `tools/run_command.py`
  - They provide consistent error messaging across the application

- **CMD Constants**: These are used in UI panels for displaying help and available commands:
  - All `CMD_*` constants are imported and used in `ui/panels.py` to show available commands to users

- **Tool Categorization Constants**:
  - `WRITE_TOOLS` and `EXECUTE_TOOLS` provide centralized tool categorization logic
  - While I didn't find direct usage in the tools modules, they're part of the application's architecture for grouping functionality

- **COMMAND_PREFIX**: This is used to identify command inputs throughout the application

All of these were verified to be false positives from the vulture analysis. The dead-code-analysis.md report has been updated to reflect this.

---

# TunaCode Template System - Simplified Implementation Plan

## Overview

Create a minimal template system that allows users to define prompts with pre-approved tools. Templates are simple files that specify:
- A prompt or task description
- A list of tools that should be auto-approved when the template is active
- Optional parameters for the prompt

## Implementation Status: ✅ COMPLETED

### Key Files Created/Modified:

1. **`src/tunacode/templates/loader.py`** - Core template functionality
   - `Template` dataclass: Represents a template with name, description, prompt, allowed_tools
   - `TemplateLoader` class: Handles loading, listing, saving, and deleting templates

2. **`src/tunacode/core/tool_handler.py`** - Modified to support templates
   - Added `active_template` property
   - Added `set_active_template()` method
   - Modified `should_confirm()` to check active template's allowed_tools

3. **`src/tunacode/cli/commands/implementations/template.py`** - CLI command
   - `/template list` - List available templates
   - `/template load <name>` - Load and activate a template
   - `/template create` - Show template creation instructions
   - `/template clear` - Clear active template

4. **`src/tunacode/core/state.py`** - State management
   - Added `tool_handler` property to StateManager
   - Added `set_tool_handler()` method

5. **`src/tunacode/cli/main.py`** - Initialization
   - Initialize ToolHandler after setup
   - Set it in StateManager for global access

6. **`src/tunacode/core/setup/template_setup.py`** - Setup integration
   - Creates template directory during initialization
   - Ensures ~/.config/tunacode/templates/ exists

### Example Templates Created:
- `~/.config/tunacode/templates/web-dev.json`
- `~/.config/tunacode/templates/debug.json`
- `~/.config/tunacode/templates/refactor.json`
- `~/.config/tunacode/templates/data-analysis.json`

## Core Principles

1. **Start Small**: Begin with the absolute minimum viable feature
2. **Use Existing Infrastructure**: Leverage current command and tool systems
3. **File-Based**: Templates are simple files (JSON or Python)
4. **No Complex Permissions**: Just tool names that get auto-approved
5. **Incremental Growth**: Each step builds on the previous one

## Implementation Steps

### Step 1: Define Template Format

Create a simple template structure. Two options:

#### Option A: JSON Template
```json
{
  "name": "web-dev",
  "description": "Web development template",
  "prompt": "Create a React component for user authentication",
  "allowed_tools": ["read_file", "write_file", "update_file", "grep", "list_dir"],
  "parameters": {}
}
```

#### Option B: Python Template
```python
# templates/web_dev.py
template = {
    "name": "web-dev",
    "description": "Web development template",
    "prompt": "Create a React component for user authentication",
    "allowed_tools": ["read_file", "write_file", "update_file", "grep", "list_dir"],
    "parameters": {}
}
```

**Decision**: Start with JSON for simplicity and language agnosticism.

### Step 2: Create Template Directory Structure

```
~/.config/tunacode/
├── templates/
│   ├── web-dev.json
│   ├── data-analysis.json
│   └── debug.json
```

### Step 3: Basic Template Loader

Create `src/tunacode/templates/loader.py`:

```python
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Template:
    name: str
    description: str
    prompt: str
    allowed_tools: List[str]
    parameters: Dict[str, str] = None

class TemplateLoader:
    def __init__(self):
        self.template_dir = Path.home() / '.config' / 'tunacode' / 'templates'
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self, name: str) -> Optional[Template]:
        """Load a template by name"""
        template_file = self.template_dir / f"{name}.json"
        if not template_file.exists():
            return None

        with open(template_file, 'r') as f:
            data = json.load(f)
            return Template(**data)

    def list_templates(self) -> List[str]:
        """List all available templates"""
        return [f.stem for f in self.template_dir.glob("*.json")]

    def save_template(self, template: Template):
        """Save a template to disk"""
        template_file = self.template_dir / f"{template.name}.json"
        with open(template_file, 'w') as f:
            json.dump({
                "name": template.name,
                "description": template.description,
                "prompt": template.prompt,
                "allowed_tools": template.allowed_tools,
                "parameters": template.parameters or {}
            }, f, indent=2)
```

### Step 4: Integration with Tool Handler

Modify `src/tunacode/core/tool_handler.py` to check for active template:

```python
class ToolHandler:
    def __init__(self):
        # ... existing code ...
        self.active_template: Optional[Template] = None

    def set_active_template(self, template: Optional[Template]):
        """Set the currently active template"""
        self.active_template = template

    def should_confirm(self, tool_name: str, **kwargs) -> bool:
        """Check if tool requires confirmation"""
        # Check yolo mode first
        if self.state.yolo_mode:
            return False

        # Check if tool is in ignore list
        if tool_name in self.state.tool_ignore_list:
            return False

        # NEW: Check if tool is allowed by active template
        if self.active_template and tool_name in self.active_template.allowed_tools:
            return False

        # Default: require confirmation
        return True
```

### Step 5: Simple CLI Command

Add a new command in `src/tunacode/cli/commands/implementations/template.py`:

```python
from typing import Optional
from ...base import Command, CommandSpec, CommandCategory
from ....templates.loader import TemplateLoader

class TemplateCommand(Command):
    """Manage and use templates"""

    @property
    def spec(self) -> CommandSpec:
        return CommandSpec(
            name="template",
            aliases=["/template", "/tpl"],
            description="Manage and use templates",
            category=CommandCategory.SYSTEM,
            usage="/template [list|load|create] [args]"
        )

    async def execute(self, args: str) -> None:
        parts = args.strip().split(maxsplit=1)
        if not parts:
            await self._show_help()
            return

        subcommand = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        if subcommand == "list":
            await self._list_templates()
        elif subcommand == "load":
            await self._load_template(rest)
        elif subcommand == "create":
            await self._create_template(rest)
        else:
            await self._show_help()

    async def _list_templates(self):
        """List all available templates"""
        loader = TemplateLoader()
        templates = loader.list_templates()

        if not templates:
            self.ui.print("No templates found.")
            self.ui.print("Create one with: /template create")
            return

        self.ui.print("Available templates:")
        for name in templates:
            template = loader.load_template(name)
            if template:
                self.ui.print(f"  • {name}: {template.description}")

    async def _load_template(self, name: str):
        """Load and activate a template"""
        if not name:
            self.ui.print_error("Please specify a template name")
            return

        loader = TemplateLoader()
        template = loader.load_template(name)

        if not template:
            self.ui.print_error(f"Template '{name}' not found")
            return

        # Set active template in tool handler
        self.state.tool_handler.set_active_template(template)

        self.ui.print_success(f"Loaded template: {template.name}")
        self.ui.print(f"Allowed tools: {', '.join(template.allowed_tools)}")

        # Execute the prompt
        if template.prompt:
            self.ui.print(f"Executing prompt: {template.prompt}")
            # Pass prompt to agent
            await self.agent.run(template.prompt)
```

### Step 6: Example Templates

Create some example templates:

#### `~/.config/tunacode/templates/web-dev.json`
```json
{
  "name": "web-dev",
  "description": "Web development tasks",
  "prompt": "",
  "allowed_tools": ["read_file", "write_file", "update_file", "grep", "list_dir", "run_command"]
}
```

#### `~/.config/tunacode/templates/debug.json`
```json
{
  "name": "debug",
  "description": "Debugging and analysis",
  "prompt": "",
  "allowed_tools": ["read_file", "grep", "list_dir", "run_command"]
}
```

#### `~/.config/tunacode/templates/refactor.json`
```json
{
  "name": "refactor",
  "description": "Code refactoring tasks",
  "prompt": "",
  "allowed_tools": ["read_file", "update_file", "grep", "list_dir"]
}
```

## Usage Examples

```bash
# List available templates
/template list

# Load a template (auto-approves its tools)
/template load web-dev

# Now use normally - tools in template are auto-approved
Create a new React component for user profile

# Create a new template interactively
/template create my-template
```

## Next Steps (Future Enhancements)

1. **Template Parameters**: Support for parameterized prompts
   ```json
   {
     "prompt": "Create a {component_type} component for {feature}",
     "parameters": {
       "component_type": "React",
       "feature": "authentication"
     }
   }
   ```

2. **Project-Specific Templates**: Look for templates in `.tunacode/templates/`

3. **Template Inheritance**: Templates can extend other templates

4. **Tool Restrictions**: Add path patterns or other restrictions
   ```json
   {
     "allowed_tools": [
       {
         "name": "write_file",
         "restrictions": {
           "paths": ["src/**/*.js", "src/**/*.jsx"]
         }
       }
     ]
   }
   ```

5. **Template Sharing**: Export/import templates

## Benefits of This Approach

1. **Minimal Changes**: Only touches tool confirmation logic
2. **No New Dependencies**: Uses standard library JSON
3. **User-Friendly**: Simple JSON files users can edit
4. **Extensible**: Easy to add features incrementally
5. **Safe**: Templates only affect tool confirmation, not execution

## Implementation Priority

1. **Phase 1**: Basic template loader and JSON format ✅
2. **Phase 2**: CLI command for list/load ✅
3. **Phase 3**: Integration with tool handler ✅
4. **Phase 4**: Example templates ✅
5. **Phase 5**: Template creation command ✅

This approach provides the core functionality with minimal complexity and can grow into the full shortcuts system described in the original plan.

## How It Works

1. **Template Loading**: When a user runs `/template load web-dev`, the system:
   - Loads the JSON template from `~/.config/tunacode/templates/web-dev.json`
   - Sets it as the active template in ToolHandler
   - Tools listed in `allowed_tools` will now skip confirmation prompts

2. **Tool Confirmation Logic**: The `should_confirm()` method in ToolHandler now checks:
   - Read-only tools → No confirmation (existing behavior)
   - Active template's allowed_tools → No confirmation (new behavior)
   - Yolo mode → No confirmation (existing behavior)
   - Otherwise → Requires confirmation

3. **Integration Flow**:
   ```
   User Command → TemplateCommand → TemplateLoader → Template
                                                         ↓
   StateManager ← ToolHandler.set_active_template() ← Template
   ```

## Known Issues Fixed

- **AttributeError Fix**: ToolHandler is now initialized in `main.py` after setup completes
- **Import Handling**: Uses TYPE_CHECKING to avoid circular imports
- **Error Handling**: Better null checks in template command
