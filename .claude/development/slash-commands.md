# Slash Command System

## Overview
Extensible command infrastructure in `src/tunacode/cli/commands/slash/` supporting auto-discovery and hot-reloading.

## Architecture
- **command.py**: Base command interface and metadata
- **loader.py**: Dynamic command discovery from `.claude/commands/`
- **processor.py**: Command execution and routing
- **validator.py**: Input validation and parsing

## Command Format
Commands stored as markdown files in `.claude/commands/`:
```yaml
command: /name
parameters:
  - name: param1
    required: true
---
Command logic here
```

## Built-in Commands
- `/deploy` - Deployment workflows
- `/github-issue` - GitHub issue management
- `/smells` - Code smell detection
- `/work` - Task management
- `/workflow` - Workflow automation

## Key Features
- Hot-reload on file changes
- Parameter validation
- Error handling with suggestions
- Extensible via markdown files
