# Creating Custom Commands

This guide walks you through creating custom commands for TunaCode, covering both built-in commands and slash commands.

## Overview

TunaCode supports two types of custom commands:

1. **Built-in Commands**: Python-based commands integrated into the codebase
2. **Slash Commands**: Markdown-based commands that can be created without modifying code

## Creating Built-in Commands

Built-in commands are ideal when you need:
- Complex logic or state manipulation
- Integration with TunaCode internals
- Performance-critical operations
- Commands that ship with TunaCode

### Step 1: Create the Command Class

Create a new file in `src/tunacode/cli/commands/implementations/`:

```python
# src/tunacode/cli/commands/implementations/mycommand.py
from typing import Optional
from ....ui import console as ui
from ..base import CommandCategory, CommandSpec, SimpleCommand

class MyCommand(SimpleCommand):
    """My custom command implementation."""

    spec = CommandSpec(
        name="mycommand",
        aliases=["/mycommand", "mc"],  # Optional aliases
        description="Does something useful",
        category=CommandCategory.DEVELOPMENT  # Choose appropriate category
    )

    async def execute(self, args: List[str], context: CommandContext) -> Optional[str]:
        """Execute the command logic."""
        # Access state
        state = context.state_manager.session

        # Parse arguments
        if not args:
            await ui.error("Please provide an argument")
            return None

        # Do something useful
        result = process_something(args[0])

        # Display output
        await ui.success(f"Processed: {result}")

        # Optional: Return special values
        # return "restart"  # Restarts the REPL
        # return "some text"  # Processes as new input
        return None  # Normal completion
```

### Step 2: Register the Command

Add your command to the registry in `src/tunacode/cli/commands/registry.py`:

1. Import your command class:
```python
from .implementations.mycommand import MyCommand
```

2. Add to the `_discover_builtin_commands` method:
```python
command_classes = [
    # ... existing commands ...
    MyCommand,  # Add your command here
]
```

### Step 3: Export the Command

Update `src/tunacode/cli/commands/implementations/__init__.py`:

```python
from .mycommand import MyCommand

__all__ = [
    # ... existing exports ...
    "MyCommand",
]
```

### Command Best Practices

1. **Error Handling**:
```python
try:
    result = risky_operation()
except SpecificError as e:
    await ui.error(f"Operation failed: {e}")
    return None
```

2. **Argument Validation**:
```python
if len(args) < 2:
    await ui.error("Usage: /mycommand <arg1> <arg2>")
    await ui.muted("Example: /mycommand foo bar")
    return None
```

3. **State Access**:
```python
# Read state
current_model = context.state_manager.session.current_model

# Modify state
context.state_manager.session.custom_value = "something"
```

4. **User Feedback**:
```python
# Different message types
await ui.info("Information message")
await ui.success("Success message")
await ui.warning("Warning message")
await ui.error("Error message")
await ui.muted("Subtle message")
```

## Creating Slash Commands

Slash commands are perfect for:
- User-specific workflows
- Team-shared commands
- Quick prototypes
- Commands that don't need code changes

### Basic Slash Command

Create a markdown file in one of these directories:
- `.tunacode/commands/` (project-specific)
- `~/.tunacode/commands/` (user-specific)

Example: `.tunacode/commands/review.md`

```markdown
Please review the following code files and provide feedback on:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Suggestions for improvement

Files to review: $ARGUMENTS
```

Usage: `/project:review src/main.py src/utils.py`

### Advanced Slash Command

With YAML frontmatter and template features:

```markdown
---
description: "Generate comprehensive test cases"
allowed-tools: ["read_file", "write_file", "grep"]
timeout: 60
parameters:
  max_context_size: 50000
  max_files: 20
---

# Test Generation Task

Generate comprehensive test cases for the following module: $ARGUMENTS

## Context

Current test files:
@@**/*test*.py

## Requirements

1. Cover all public functions and methods
2. Include edge cases and error conditions
3. Follow the existing test patterns
4. Use pytest fixtures where appropriate

## Module to test

@$ARGUMENTS

Please create or update the appropriate test file.
```

### Template Syntax

Slash commands support several template features:

1. **Variable Substitution**:
   - `$ARGUMENTS` - Replaced with command arguments
   - `$ENV_VAR` - Environment variable (e.g., `$HOME`, `$USER`)

2. **Command Execution**:
   - `!`ls -la`` - Execute shell command and include output

3. **File Inclusion**:
   - `@path/to/file.py` - Include file contents
   - `@@**/*.py` - Include files matching glob pattern

### Organizing Slash Commands

Use subdirectories to organize commands:

```
.tunacode/commands/
├── dev/
│   ├── test.md       # /project:dev:test
│   └── lint.md       # /project:dev:lint
├── docs/
│   ├── generate.md   # /project:docs:generate
│   └── update.md     # /project:docs:update
└── review.md         # /project:review
```

### Slash Command Tips

1. **Use Descriptive Names**: Choose clear, action-oriented names
2. **Add Descriptions**: Always include a description in frontmatter
3. **Limit Scope**: Use `allowed-tools` to restrict available tools
4. **Set Timeouts**: Prevent long-running commands with timeout
5. **Context Limits**: Set reasonable limits for file inclusion

## Command Development Workflow

### For Built-in Commands

1. Create command class with minimal implementation
2. Register and test basic functionality
3. Iterate on features and error handling
4. Add comprehensive documentation

### For Slash Commands

1. Create markdown file in command directory
2. Test with `/project:commandname` (or appropriate namespace)
3. Use `/command-reload` to reload changes
4. Refine template and parameters
5. Share with team by committing to repository

## Debugging Commands

### Built-in Commands

Use logging for debugging:

```python
import logging
logger = logging.getLogger(__name__)

class MyCommand(SimpleCommand):
    async def execute(self, args, context):
        logger.debug(f"Executing with args: {args}")
        # ... implementation ...
```

### Slash Commands

Enable thought display to see template processing:

```
/thoughts
/project:mycommand test
```

## Examples

### Example 1: Git Helper Command

Built-in command for git operations:

```python
class GitStatusCommand(SimpleCommand):
    spec = CommandSpec(
        name="gs",
        aliases=["/gs", "gitstatus"],
        description="Show git status with useful filters",
        category=CommandCategory.DEVELOPMENT
    )

    async def execute(self, args, context):
        import subprocess

        # Run git status
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            await ui.error("Not in a git repository")
            return None

        # Parse and display
        lines = result.stdout.strip().split('\n')
        modified = [l for l in lines if l.startswith(' M')]
        untracked = [l for l in lines if l.startswith('??')]

        await ui.info(f"Modified files: {len(modified)}")
        for line in modified:
            await ui.muted(f"  {line}")

        await ui.info(f"Untracked files: {len(untracked)}")
        for line in untracked[:5]:  # Show first 5
            await ui.muted(f"  {line}")

        return None
```

### Example 2: Code Analysis Slash Command

`.tunacode/commands/analyze/complexity.md`:

```markdown
---
description: "Analyze code complexity and suggest improvements"
allowed-tools: ["read_file", "grep"]
---

# Code Complexity Analysis

Analyze the complexity of the following Python file and suggest improvements:

File: @$ARGUMENTS

Please examine:
1. Cyclomatic complexity of functions
2. Deeply nested code blocks
3. Long functions that could be split
4. Repeated code patterns

Provide specific suggestions for refactoring complex areas.
```

### Example 3: Project Setup Command

`.tunacode/commands/setup/django.md`:

```markdown
---
description: "Setup a new Django project with best practices"
allowed-tools: ["write_file", "bash"]
timeout: 120
---

# Django Project Setup

Create a new Django project named: $ARGUMENTS

Setup should include:
1. Project structure following Django best practices
2. Basic settings configuration (settings/base.py, dev.py, prod.py)
3. Requirements files (base.txt, dev.txt, prod.txt)
4. Pre-commit configuration
5. Basic .gitignore
6. README.md with setup instructions
7. Docker configuration (Dockerfile and docker-compose.yml)

Use Django 5.0+ and Python 3.11+.
```

## Troubleshooting

### Command Not Found

1. Check command is registered in registry
2. Verify name and aliases are correct
3. Try `/command-reload` for slash commands
4. Check for typos in command name

### Command Execution Errors

1. Check logs for detailed errors
2. Verify argument parsing logic
3. Test with `/thoughts` enabled
4. Add debug logging to isolate issues

### Slash Command Issues

1. Validate YAML frontmatter syntax
2. Check file permissions and location
3. Look for conflict warnings in logs
4. Test template variables separately

## See Also

- [Command System Architecture](command-system-architecture.md) - Technical details
- [User Commands](../user/commands.md) - User documentation
- [TunaCode Development](codebase-hygiene.md) - Development practices
