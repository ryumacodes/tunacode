# Command System Architecture

This document provides a comprehensive technical overview of TunaCode's command system, including its architecture, components, and extension mechanisms.

## Overview

The TunaCode command system is a sophisticated, extensible framework that supports both built-in commands and user-defined slash commands. It provides a unified interface for executing various operations within the TunaCode CLI.

## Architecture Components

### 1. Base Infrastructure (`src/tunacode/cli/commands/base.py`)

The foundation of the command system consists of:

- **`Command`**: Abstract base class defining the command interface
  - Properties: `name`, `aliases`, `description`, `category`
  - Method: `execute(args, context)`

- **`SimpleCommand`**: Convenience base class for standard commands
  - Uses `CommandSpec` for metadata
  - Reduces boilerplate for simple commands

- **`CommandSpec`**: Dataclass for command metadata
  - Fields: `name`, `aliases`, `description`, `category`

- **`CommandCategory`**: Enum for organizing commands
  - Categories: `SYSTEM`, `NAVIGATION`, `DEVELOPMENT`, `MODEL`, `DEBUG`

### 2. Command Registry (`src/tunacode/cli/commands/registry.py`)

The central hub for command management:

#### Key Features:
- **Auto-discovery**: Automatically discovers and registers commands
- **Partial matching**: Supports abbreviated command names
- **Category organization**: Groups commands by functionality
- **Dependency injection**: Via `CommandFactory` and `CommandDependencies`
- **Hot reloading**: Dynamic reloading of slash commands

#### Core Methods:
```python
- register(command): Register a command instance
- discover_commands(): Auto-discover all commands
- execute(command_text, context): Execute a command
- find_matching_commands(partial): Find commands by partial name
- is_command(text): Check if text is a command
```

### 3. Command Types

#### Built-in Commands (`src/tunacode/cli/commands/implementations/`)

Statically defined commands organized by functionality:

- **System Commands** (`system.py`): `/help`, `/clear`, `/refresh`, `/update`
- **Development Commands** (`development.py`): `/branch`, `/init`
- **Debug Commands** (`debug.py`): `/dump`, `/thoughts`, `/iterations`, `/fix`
- **Model Commands** (`model.py`): `/model`
- **Planning Commands** (`plan.py`): `/plan`, `/exit-plan`
- **Other Commands**: `/todo`, `/compact`, `/command-reload`

#### Slash Commands (`src/tunacode/cli/commands/slash/`)

Markdown-based custom commands with advanced features:

**Components:**
- **`SlashCommand`**: Command implementation for markdown files
- **`SlashCommandLoader`**: Discovers and loads commands from directories
- **`MarkdownTemplateProcessor`**: Processes templates with variables
- **`CommandValidator`**: Validates command security and syntax

**Discovery Locations (by priority):**
1. `.tunacode/commands/` in project directory
2. `.claude/commands/` in project directory
3. `~/.tunacode/commands/` in user home
4. `~/.claude/commands/` in user home

### 4. Command Execution Flow

```
1. User Input Detection
   └─ Line starts with "/" → Command mode

2. Command Registry Lookup
   ├─ Exact match → Execute command
   └─ Partial match → Find candidates
       ├─ Single match → Execute command
       └─ Multiple matches → Show suggestions

3. Command Execution
   ├─ Create CommandContext
   ├─ Call command.execute(args, context)
   └─ Handle return value
       ├─ "restart" → Restart REPL
       ├─ String → Process as new input
       └─ None → Continue normally
```

### 5. Slash Command Features

#### Template Processing

Slash commands support advanced template features:

- **`$ARGUMENTS`**: Replaced with command arguments
- **`$ENV_VAR`**: Environment variable substitution
- **`!`command``**: Execute shell commands
- **`@file`**: Include file contents
- **`@@pattern`**: Include files matching glob pattern

#### YAML Frontmatter

Commands can include metadata:
```yaml
---
description: "Command description"
allowed-tools: ["read_file", "grep"]
timeout: 30
parameters:
  max_context_size: 100000
  max_files: 50
---
```

#### Security Features

- Command validation before execution
- Tool restrictions via `allowed-tools`
- Context size limits
- File inclusion limits

### 6. Extension Points

#### Adding Built-in Commands

1. Create a new class in `implementations/`:
```python
class MyCommand(SimpleCommand):
    spec = CommandSpec(
        name="mycommand",
        aliases=["/mycommand", "mc"],
        description="My custom command",
        category=CommandCategory.DEVELOPMENT
    )

    async def execute(self, args, context):
        # Implementation
        return None
```

2. Register in `CommandRegistry._discover_builtin_commands()`

#### Creating Slash Commands

1. Create a markdown file in a command directory
2. Add optional YAML frontmatter
3. Write the command template
4. Command is auto-discovered on startup

### 7. Command Context

The `CommandContext` provides access to:
- `state_manager`: Current session state
- `process_request`: Callback for processing AI requests
- Additional context as needed

### 8. Special Features

#### Command Aliases
- Primary name and multiple aliases
- Case-insensitive matching
- Slash prefix optional for built-in commands

#### Partial Matching
- Type `/h` to match `/help`
- Ambiguous matches show suggestions
- Improves command discovery UX

#### Hot Reloading
- `/command-reload` reloads slash commands
- Useful for development and testing
- No restart required

#### Template Shortcuts
- Dynamic command aliases from templates
- Loaded from template system
- Integrated with command registry

## Best Practices

1. **Command Design**
   - Keep commands focused and single-purpose
   - Use descriptive names and aliases
   - Provide helpful descriptions
   - Choose appropriate categories

2. **Error Handling**
   - Validate arguments early
   - Provide clear error messages
   - Use `ValidationError` for user errors
   - Log technical errors appropriately

3. **State Management**
   - Access state via `context.state_manager`
   - Don't modify global state directly
   - Use return values for flow control

4. **Security**
   - Validate all user input
   - Use tool restrictions for slash commands
   - Limit context injection sizes
   - Sanitize command execution

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Input ("/command")               │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    REPL Handler                          │
│                 (detects "/" prefix)                     │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Command Registry                        │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Lookup    │  │   Factory    │  │  Discovery    │  │
│  │  & Match    │  │ & Dependencies│  │  & Loading    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────────┐
│   Built-in Commands   │   │     Slash Commands        │
│  ┌─────────────────┐  │   │  ┌────────────────────┐  │
│  │ SimpleCommand   │  │   │  │ SlashCommand       │  │
│  │ Implementations │  │   │  │ + Template Processor│  │
│  └─────────────────┘  │   │  └────────────────────┘  │
└───────────────────────┘   └───────────────────────────┘
            │                           │
            └─────────────┬─────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Command Execution                       │
│                 (with CommandContext)                    │
└─────────────────────────────────────────────────────────┘
```

## See Also

- [Creating Custom Commands](creating-custom-commands.md) - Step-by-step guide
- [User Commands](../user/commands.md) - User-facing command documentation
