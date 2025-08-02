# TunaCode Shortcuts System Implementation Plan

## Executive Summary

This implementation plan details how to add a `/shortcuts` command system to TunaCode that allows users to define predefined tool sets with pre-approved permissions. The design follows common CLI patterns, integrates with existing permission systems, and provides persistent storage for shortcut definitions. The system will enable users to bypass tool confirmations for trusted workflows while maintaining security boundaries.

## System Architecture Overview

The shortcuts system consists of four main components:
1. **Command Infrastructure** - New command classes for shortcuts management
2. **Configuration Storage** - YAML-based persistent shortcut definitions
3. **Permission Integration** - Hooks into the existing tool confirmation flow
4. **Runtime Management** - Activation and execution of shortcuts

## 1. Command System Implementation

### Base Shortcut Command Structure

Create a new file `src/tunacode/cli/commands/shortcuts.py`:

```python
from typing import List, Optional, Dict, Any
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from ..base import BaseCommand  # Assuming base command exists
from ...core.config import ConfigManager
from ...core.tool_handler import ToolHandler
from ...ui.tool_ui import ToolConfirmationUI

@dataclass
class ToolPermission:
    """Represents permission for a specific tool"""
    tool_name: str
    auto_approve: bool = True
    parameters: Optional[Dict[str, Any]] = None
    restrictions: Optional[List[str]] = None

@dataclass
class Shortcut:
    """Represents a shortcut configuration"""
    name: str
    description: str
    tools: List[ToolPermission]
    created_at: str
    created_by: str
    version: str = "1.0"
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert ToolPermission objects to dicts
        data['tools'] = [asdict(tool) for tool in self.tools]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Shortcut':
        # Convert tool dicts back to ToolPermission objects
        tools = [ToolPermission(**tool) for tool in data.get('tools', [])]
        data['tools'] = tools
        return cls(**data)

class ShortcutsCommand(BaseCommand):
    """Main shortcuts command handler"""

    def __init__(self):
        super().__init__()
        self.name = "shortcuts"
        self.description = "Manage tool permission shortcuts"
        self.subcommands = {
            'create': self.create_shortcut,
            'list': self.list_shortcuts,
            'activate': self.activate_shortcut,
            'delete': self.delete_shortcut,
            'show': self.show_shortcut,
            'edit': self.edit_shortcut
        }
        self.shortcuts_manager = ShortcutsManager()

    def setup_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='subcommand', help='Shortcuts subcommands')

        # Create subcommand
        create_parser = subparsers.add_parser('create', help='Create a new shortcut')
        create_parser.add_argument('name', help='Shortcut name')
        create_parser.add_argument('--description', '-d', help='Shortcut description', required=True)
        create_parser.add_argument('--tools', '-t', nargs='+', help='Tools to pre-approve', required=True)
        create_parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')

        # List subcommand
        list_parser = subparsers.add_parser('list', help='List all shortcuts')
        list_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed info')

        # Activate subcommand
        activate_parser = subparsers.add_parser('activate', help='Activate a shortcut')
        activate_parser.add_argument('name', help='Shortcut name to activate')
        activate_parser.add_argument('prompt', nargs='*', help='Original prompt to pass through')

        # Delete subcommand
        delete_parser = subparsers.add_parser('delete', help='Delete a shortcut')
        delete_parser.add_argument('name', help='Shortcut name to delete')

        # Show subcommand
        show_parser = subparsers.add_parser('show', help='Show shortcut details')
        show_parser.add_argument('name', help='Shortcut name to show')

        # Edit subcommand
        edit_parser = subparsers.add_parser('edit', help='Edit an existing shortcut')
        edit_parser.add_argument('name', help='Shortcut name to edit')
        edit_parser.add_argument('--add-tools', nargs='+', help='Add tools to shortcut')
        edit_parser.add_argument('--remove-tools', nargs='+', help='Remove tools from shortcut')

    def execute(self, args):
        if not args.subcommand:
            self.print_help()
            return

        handler = self.subcommands.get(args.subcommand)
        if handler:
            return handler(args)
        else:
            self.print_error(f"Unknown subcommand: {args.subcommand}")
```

### Shortcuts Manager Implementation

```python
class ShortcutsManager:
    """Manages shortcut storage and operations"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or self._get_default_config_dir()
        self.shortcuts_file = self.config_dir / "shortcuts.yml"
        self.active_shortcuts = set()
        self._ensure_config_dir()

    def _get_default_config_dir(self) -> Path:
        """Get the default configuration directory"""
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', '~'))
        else:  # Unix-like
            base = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config'))

        return base.expanduser() / 'tunacode'

    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_shortcuts(self) -> Dict[str, Shortcut]:
        """Load shortcuts from configuration file"""
        if not self.shortcuts_file.exists():
            return {}

        try:
            with open(self.shortcuts_file, 'r') as f:
                data = yaml.safe_load(f) or {}
                shortcuts = {}
                for name, shortcut_data in data.get('shortcuts', {}).items():
                    shortcuts[name] = Shortcut.from_dict(shortcut_data)
                return shortcuts
        except Exception as e:
            print(f"Error loading shortcuts: {e}")
            return {}

    def save_shortcuts(self, shortcuts: Dict[str, Shortcut]):
        """Save shortcuts to configuration file"""
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'shortcuts': {
                name: shortcut.to_dict()
                for name, shortcut in shortcuts.items()
            }
        }

        # Create backup before saving
        if self.shortcuts_file.exists():
            backup_file = self.shortcuts_file.with_suffix('.yml.backup')
            shutil.copy2(self.shortcuts_file, backup_file)

        with open(self.shortcuts_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def create_shortcut(self, name: str, description: str, tools: List[str],
                       user: str = None) -> Shortcut:
        """Create a new shortcut"""
        shortcuts = self.load_shortcuts()

        if name in shortcuts:
            raise ValueError(f"Shortcut '{name}' already exists")

        # Create tool permissions
        tool_permissions = [
            ToolPermission(tool_name=tool, auto_approve=True)
            for tool in tools
        ]

        shortcut = Shortcut(
            name=name,
            description=description,
            tools=tool_permissions,
            created_at=datetime.now().isoformat(),
            created_by=user or os.environ.get('USER', 'unknown')
        )

        shortcuts[name] = shortcut
        self.save_shortcuts(shortcuts)
        return shortcut

    def activate_shortcut(self, name: str) -> Shortcut:
        """Activate a shortcut and return its configuration"""
        shortcuts = self.load_shortcuts()

        if name not in shortcuts:
            raise ValueError(f"Shortcut '{name}' not found")

        shortcut = shortcuts[name]
        self.active_shortcuts.add(name)

        # Apply tool permissions to the current session
        self._apply_tool_permissions(shortcut)

        return shortcut

    def _apply_tool_permissions(self, shortcut: Shortcut):
        """Apply tool permissions from a shortcut to the current session"""
        # This would integrate with the existing tool_handler
        # For now, we'll store in a session context
        from ...core.session import SessionContext

        session = SessionContext.get_current()
        if not hasattr(session, 'tool_permissions'):
            session.tool_permissions = {}

        for tool_perm in shortcut.tools:
            session.tool_permissions[tool_perm.tool_name] = {
                'auto_approve': tool_perm.auto_approve,
                'parameters': tool_perm.parameters,
                'restrictions': tool_perm.restrictions,
                'source': f'shortcut:{shortcut.name}'
            }
```

## 2. Integration with Tool Confirmation System

### Modified Tool Handler

Create hooks in `src/tunacode/core/tool_handler.py`:

```python
class ToolHandler:
    """Enhanced tool handler with shortcuts support"""

    def __init__(self, ui: Optional[ToolConfirmationUI] = None):
        self.ui = ui or ToolConfirmationUI()
        self.tool_ignore_list = set()
        self.session_permissions = {}
        self.yolo_mode = False

    def should_request_confirmation(self, tool_name: str, context: Dict[str, Any]) -> bool:
        """Check if tool requires confirmation"""
        # Check yolo mode first
        if self.yolo_mode:
            return False

        # Check if tool is in ignore list
        if tool_name in self.tool_ignore_list:
            return False

        # Check session permissions from shortcuts
        if tool_name in self.session_permissions:
            perm = self.session_permissions[tool_name]
            if perm.get('auto_approve', False):
                # Check if any restrictions apply
                if restrictions := perm.get('restrictions'):
                    if not self._check_restrictions(tool_name, context, restrictions):
                        return True  # Restrictions not met, require confirmation
                return False  # Auto-approved

        # Default: require confirmation
        return True

    def _check_restrictions(self, tool_name: str, context: Dict[str, Any],
                          restrictions: List[str]) -> bool:
        """Check if tool usage meets restrictions"""
        for restriction in restrictions:
            if restriction.startswith('max_files:'):
                max_files = int(restriction.split(':')[1])
                if context.get('file_count', 0) > max_files:
                    return False
            elif restriction.startswith('path_pattern:'):
                pattern = restriction.split(':', 1)[1]
                if not fnmatch.fnmatch(context.get('path', ''), pattern):
                    return False
            # Add more restriction types as needed
        return True

    def load_shortcuts_permissions(self):
        """Load permissions from active shortcuts"""
        from ..cli.commands.shortcuts import ShortcutsManager
        manager = ShortcutsManager()

        # Get active shortcuts from session or state
        session = SessionContext.get_current()
        active_shortcuts = getattr(session, 'active_shortcuts', [])

        for shortcut_name in active_shortcuts:
            try:
                shortcut = manager.load_shortcuts().get(shortcut_name)
                if shortcut:
                    for tool_perm in shortcut.tools:
                        self.session_permissions[tool_perm.tool_name] = {
                            'auto_approve': tool_perm.auto_approve,
                            'parameters': tool_perm.parameters,
                            'restrictions': tool_perm.restrictions,
                            'source': f'shortcut:{shortcut_name}'
                        }
            except Exception as e:
                print(f"Error loading shortcut {shortcut_name}: {e}")
```

### Enhanced State Manager

```python
class StateManager:
    """Enhanced state manager with shortcuts support"""

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or self._get_default_state_file()
        self.state = self._load_state()

    def _get_default_state_file(self) -> Path:
        config_dir = Path.home() / '.config' / 'tunacode'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'state.json'

    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'tool_ignore_list': [],
            'active_shortcuts': [],
            'yolo_mode': False,
            'session_id': None
        }

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def activate_shortcut(self, shortcut_name: str):
        """Add shortcut to active shortcuts"""
        if shortcut_name not in self.state['active_shortcuts']:
            self.state['active_shortcuts'].append(shortcut_name)
            self.save_state()

    def deactivate_shortcut(self, shortcut_name: str):
        """Remove shortcut from active shortcuts"""
        if shortcut_name in self.state['active_shortcuts']:
            self.state['active_shortcuts'].remove(shortcut_name)
            self.save_state()

    def get_active_shortcuts(self) -> List[str]:
        """Get list of active shortcuts"""
        return self.state.get('active_shortcuts', [])
```

## 3. Configuration Storage Format

### Shortcuts Configuration File Structure

Location: `~/.config/tunacode/shortcuts.yml`

```yaml
version: "1.0"
last_updated: "2025-08-02T10:30:00Z"
shortcuts:
  web-dev:
    name: "web-dev"
    description: "Web development tools with file operation permissions"
    created_at: "2025-08-02T10:00:00Z"
    created_by: "user"
    version: "1.0"
    tools:
      - tool_name: "file_create"
        auto_approve: true
        restrictions:
          - "path_pattern:src/**/*.{js,ts,jsx,tsx,css,html}"
      - tool_name: "file_edit"
        auto_approve: true
        restrictions:
          - "path_pattern:src/**/*"
          - "max_files:10"
      - tool_name: "terminal_command"
        auto_approve: true
        parameters:
          allowed_commands:
            - "npm install"
            - "npm run *"
            - "yarn *"
            - "git add"
            - "git commit"
        restrictions:
          - "no_sudo"
          - "no_rm_rf"
      - tool_name: "web_search"
        auto_approve: true

  data-analysis:
    name: "data-analysis"
    description: "Data analysis and visualization tools"
    created_at: "2025-08-02T11:00:00Z"
    created_by: "user"
    version: "1.0"
    tools:
      - tool_name: "file_read"
        auto_approve: true
        restrictions:
          - "path_pattern:data/**/*.{csv,json,xlsx}"
      - tool_name: "python_execute"
        auto_approve: true
        parameters:
          allowed_imports:
            - "pandas"
            - "numpy"
            - "matplotlib"
            - "seaborn"
        restrictions:
          - "no_file_write"
          - "memory_limit:2GB"
      - tool_name: "file_create"
        auto_approve: true
        restrictions:
          - "path_pattern:output/**/*.{png,jpg,svg,pdf}"
```

### Project-Specific Shortcuts

Location: `./.tunacode/shortcuts.yml`

```yaml
version: "1.0"
project: "my-project"
shortcuts:
  test-suite:
    name: "test-suite"
    description: "Run project test suite with auto-approval"
    tools:
      - tool_name: "terminal_command"
        auto_approve: true
        parameters:
          allowed_commands:
            - "pytest *"
            - "python -m pytest *"
            - "coverage run *"
      - tool_name: "file_read"
        auto_approve: true
        restrictions:
          - "path_pattern:tests/**/*.py"
```

## 4. Command Implementation Examples

### Create Shortcut Command

```python
def create_shortcut(self, args):
    """Create a new shortcut"""
    if args.interactive:
        return self._create_shortcut_interactive()

    try:
        # Validate tools exist
        available_tools = self._get_available_tools()
        invalid_tools = [t for t in args.tools if t not in available_tools]
        if invalid_tools:
            self.print_error(f"Invalid tools: {', '.join(invalid_tools)}")
            self.print_info(f"Available tools: {', '.join(available_tools)}")
            return

        shortcut = self.shortcuts_manager.create_shortcut(
            name=args.name,
            description=args.description,
            tools=args.tools
        )

        self.print_success(f"Created shortcut '{shortcut.name}'")
        self.print_info(f"Tools: {', '.join(args.tools)}")
        self.print_info(f"Use '/shortcuts activate {shortcut.name}' to activate")

    except ValueError as e:
        self.print_error(str(e))
```

### Activate Shortcut Command

```python
def activate_shortcut(self, args):
    """Activate a shortcut and pass through the original prompt"""
    try:
        shortcut = self.shortcuts_manager.activate_shortcut(args.name)

        # Update state manager
        state_manager = StateManager()
        state_manager.activate_shortcut(args.name)

        # Apply permissions to current session
        tool_handler = ToolHandler.get_instance()
        tool_handler.load_shortcuts_permissions()

        self.print_success(f"Activated shortcut '{shortcut.name}'")
        self.print_info(f"Pre-approved tools: {len(shortcut.tools)}")

        # Pass through the original prompt if provided
        if args.prompt:
            original_prompt = ' '.join(args.prompt)
            self.print_info(f"Executing with prompt: {original_prompt}")

            # Hand off to main command processor
            from ...cli.main import process_command
            return process_command(original_prompt)

    except ValueError as e:
        self.print_error(str(e))
```

### List Shortcuts Command

```python
def list_shortcuts(self, args):
    """List all available shortcuts"""
    shortcuts = self.shortcuts_manager.load_shortcuts()

    if not shortcuts:
        self.print_info("No shortcuts defined")
        self.print_info("Create one with: /shortcuts create <name> -d <description> -t <tools>")
        return

    # Get active shortcuts
    state_manager = StateManager()
    active_shortcuts = state_manager.get_active_shortcuts()

    for name, shortcut in shortcuts.items():
        status = "🟢 ACTIVE" if name in active_shortcuts else "⚪ INACTIVE"
        print(f"\n{status} {name}")
        print(f"  Description: {shortcut.description}")

        if args.verbose:
            print(f"  Created: {shortcut.created_at} by {shortcut.created_by}")
            print(f"  Tools ({len(shortcut.tools)}):")
            for tool in shortcut.tools:
                restrictions = f" [{', '.join(tool.restrictions)}]" if tool.restrictions else ""
                print(f"    - {tool.tool_name}{restrictions}")
```

## 5. Usage Examples

### Basic Usage

```bash
# Create a web development shortcut
/shortcuts create web-dev -d "Web development tools" -t file_create file_edit terminal_command web_search

# List all shortcuts
/shortcuts list

# Activate shortcut and run command
/shortcuts activate web-dev Create a React component for user authentication

# Show shortcut details
/shortcuts show web-dev

# Edit shortcut - add more tools
/shortcuts edit web-dev --add-tools file_delete file_move

# Delete shortcut
/shortcuts delete web-dev
```

### Interactive Creation

```bash
/shortcuts create --interactive

> Shortcut name: api-dev
> Description: API development workflow
> Select tools to pre-approve (space to select, enter to confirm):
  [x] file_create
  [x] file_edit
  [ ] file_delete
  [x] terminal_command
  [x] web_search
  [ ] python_execute

> Configure restrictions for terminal_command? (y/n): y
> Allowed command patterns (one per line, empty to finish):
  npm *
  node *.js
  curl http://localhost:*

> Shortcut 'api-dev' created successfully!
```

### Project-Specific Shortcuts

```bash
# In a project directory
cd my-project/

# Create project-specific shortcut
/shortcuts create test-runner -d "Run tests with coverage" -t terminal_command file_read --project

# This creates .tunacode/shortcuts.yml in the project
```

## 6. Integration Points

### Hook into Main Command Processor

```python
# In src/tunacode/cli/main.py
def process_command(command: str, context: Optional[Dict] = None):
    """Process user command with shortcuts support"""

    # Check if command starts with /shortcuts
    if command.startswith('/shortcuts'):
        from .commands.shortcuts import ShortcutsCommand
        cmd = ShortcutsCommand()
        args = parse_command_args(command)
        return cmd.execute(args)

    # Regular command processing continues...
```

### Tool Confirmation UI Integration

```python
# In src/tunacode/ui/tool_ui.py
class ToolConfirmationUI:
    """Enhanced UI with shortcuts awareness"""

    def show_tool_confirmation(self, tool_name: str, context: Dict) -> bool:
        """Show tool confirmation dialog"""

        # Check if tool is pre-approved by shortcut
        session = SessionContext.get_current()
        if hasattr(session, 'tool_permissions'):
            perm = session.tool_permissions.get(tool_name)
            if perm and perm.get('auto_approve'):
                source = perm.get('source', 'unknown')
                self.show_auto_approval_notice(tool_name, source)
                return True

        # Show regular confirmation dialog
        return self._show_confirmation_dialog(tool_name, context)

    def show_auto_approval_notice(self, tool_name: str, source: str):
        """Show notice that tool was auto-approved"""
        print(f"✅ Tool '{tool_name}' auto-approved by {source}")
```

## 7. Security Considerations

### Safety Mechanisms

1. **Restriction Validation**: Tools can have restrictions that are checked at runtime
2. **Audit Trail**: All auto-approvals are logged with their source
3. **Scope Limiting**: Shortcuts can limit tool usage to specific paths or parameters
4. **No Sudo/Dangerous Commands**: Built-in protection against dangerous operations
5. **Session Isolation**: Shortcuts are session-specific and don't affect other users

### Example Security Implementation

```python
class SecurityValidator:
    """Validates tool usage against security policies"""

    DANGEROUS_PATTERNS = [
        'rm -rf /',
        'sudo rm',
        'format c:',
        'del /f /s /q',
        ':(){ :|:& };:'  # Fork bomb
    ]

    def validate_command(self, command: str, restrictions: List[str]) -> bool:
        """Validate command against restrictions"""

        # Check dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command.lower():
                return False

        # Check user restrictions
        for restriction in restrictions:
            if restriction == 'no_sudo' and 'sudo' in command:
                return False
            elif restriction == 'no_rm_rf' and 'rm' in command and '-rf' in command:
                return False

        return True
```

## Conclusion

This implementation plan provides a comprehensive shortcuts system for TunaCode that:

1. **Integrates seamlessly** with the existing command structure
2. **Provides flexible permissions** with granular control
3. **Stores configurations persistently** in YAML format
4. **Maintains security** through restrictions and validation
5. **Offers intuitive usage** with clear command structure
6. **Supports both global and project-specific** shortcuts

The system balances automation convenience with security, allowing users to streamline their workflows while maintaining control over tool permissions.
