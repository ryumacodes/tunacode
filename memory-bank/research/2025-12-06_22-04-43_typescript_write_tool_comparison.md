# Research – TypeScript WriteTool vs Python File Tools Comparison

**Date:** 2025-12-06
**Owner:** Claude Code Assistant
**Phase:** Research
**Tags:** [comparison, typescript, python, file-operations, architecture]

## Goal
Compare the TypeScript WriteTool implementation with Python's file writing/updating tools to extract key patterns, architectural differences, and concepts that can improve the diff display implementation.

## Key Architectural Differences

### 1. Tool Definition Pattern

#### TypeScript (Zod-based schema)
```typescript
export const WriteTool = Tool.define("write", {
  description: DESCRIPTION,
  parameters: z.object({
    content: z.string().describe("The content to write to the file"),
    filePath: z.string().describe("The absolute path to the file to write"),
  }),
  async execute(params, ctx) {
    // implementation
  }
})
```

#### Python (Decorator-based)
```python
@file_tool
async def write_file(filepath: str, content: str) -> str:
    """Write content to a new file. Fails if the file already exists."""
    # implementation
```

**Key Differences:**
- TypeScript uses explicit Zod schema validation
- Python relies on type hints and docstrings
- TypeScript has a unified `Tool.define` pattern vs Python's decorators
- TypeScript parameters are structured objects, Python uses positional arguments

### 2. Permission System

#### TypeScript (Explicit permission checks)
```typescript
// External directory permission check
if (!Filesystem.contains(Instance.directory, filepath)) {
  if (agent.permission.external_directory === "ask") {
    await Permission.ask({
      type: "external_directory",
      pattern: [parentDir, path.join(parentDir, "*")],
      // ...metadata
    })
  } else if (agent.permission.external_directory === "deny") {
    throw new Permission.RejectedError(/*...*/)
  }
}

// Write permission check
if (agent.permission.edit === "ask")
  await Permission.ask({
    type: "write",
    title: exists ? "Overwrite this file: " + filepath : "Create new file: " + filepath,
    // ...
  })
```

#### Python (No explicit permission system)
- No permission checks before file operations
- Relies on OS-level permissions
- Only handles errors after the fact

**Key Concept for Python Implementation:**
The TypeScript permission system provides:
1. **Pre-operation validation** - checks before touching files
2. **User consent flow** - explicit ask/deny/allow modes
3. **Pattern-based permissions** - can allow entire directories
4. **Metadata tracking** - session and message IDs for audit

### 3. Rich Return Values

#### TypeScript (Structured return)
```typescript
return {
  title: path.relative(Instance.worktree, filepath),
  metadata: {
    diagnostics,
    filepath,
    exists: exists,
  },
  output,  // LSP diagnostic output
}
```

#### Python (Simple string return)
```python
return f"Successfully wrote to new file: {filepath}"
```

**Key Difference:**
- TypeScript returns structured data with metadata
- Python returns only a simple message string
- TypeScript includes LSP diagnostics in the return value
- TypeScript includes relative path for display

### 4. LSP Integration

#### TypeScript (Built-in LSP support)
```typescript
// Touch file for LSP
await LSP.touchFile(filepath, true)

// Get diagnostics for all files
const diagnostics = await LSP.diagnostics()

// Format diagnostic output
for (const [file, issues] of Object.entries(diagnostics)) {
  if (issues.length === 0) continue
  output += `\n<file_diagnostics>\n${issues.map(LSP.Diagnostic.pretty).join("\n")}\n</file_diagnostics>\n`
}
```

#### Python (No LSP integration)
- No language server protocol support
- No syntax checking or diagnostics
- No real-time error highlighting

### 5. Event System

#### TypeScript (Event-driven architecture)
```typescript
// Publish file edited event
await Bus.publish(File.Event.Edited, {
  file: filepath,
})

// Track file time for change detection
FileTime.read(ctx.sessionID, filepath)
```

#### Python (No event system)
- Direct file operations without event broadcasting
- No centralized change tracking
- No file time metadata system

### 6. File System Utilities

#### TypeScript (Rich FS utilities)
```typescript
import { Filesystem } from "../util/filesystem"

// Check if path is within working directory
Filesystem.contains(Instance.directory, filepath)

// Working tree management
Instance.directory  // Project root
Instance.worktree   // Git worktree
```

#### Python (Basic OS operations)
```python
import os

# Basic path operations
os.path.exists(filepath)
os.path.dirname(filepath)
os.makedirs(dirpath, exist_ok=True)
```

## Concepts to Import for Python Implementation

### 1. Structured Return Values
Instead of simple strings, return rich data:
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class FileOperationResult:
    title: str  # Relative path for display
    filepath: str  # Absolute path
    exists: bool  # Whether file existed before
    operation: str  # "write", "update", "create"
    metadata: Dict[str, Any]  # Additional data
    output: Optional[str] = None  # Additional output (e.g., diagnostics)

    def to_display_string(self) -> str:
        """Generate human-readable display string."""
        if self.output:
            return f"{self.title}\n{self.output}"
        return f"{self.title} ({self.operation})"
```

### 2. Permission System (Optional Enhancement)
```python
from enum import Enum
from typing import Optional

class PermissionMode(Enum):
    ASK = "ask"
    ALLOW = "allow"
    DENY = "deny"

class PermissionManager:
    def __init__(self, edit_mode: PermissionMode = PermissionMode.ALLOW,
                 external_dir_mode: PermissionMode = PermissionMode.ASK):
        self.edit_mode = edit_mode
        self.external_dir_mode = external_dir_mode

    async def check_write_permission(self, filepath: str) -> bool:
        """Check if write operation is permitted."""
        # Implementation based on working directory checks
        pass
```

### 3. Event System for File Changes
```python
from typing import Callable, List
import asyncio

class FileEventManager:
    def __init__(self):
        self._subscribers: List[Callable] = []

    def subscribe(self, callback: Callable):
        """Subscribe to file change events."""
        self._subscribers.append(callback)

    async def publish_file_edited(self, filepath: str, operation: str):
        """Notify subscribers of file change."""
        event = {
            "type": "file_edited",
            "filepath": filepath,
            "operation": operation,
            "timestamp": asyncio.get_event_loop().time()
        }
        for callback in self._subscribers:
            await callback(event)
```

### 4. Diff-Enhanced Return Value
Combining TypeScript patterns with Python diff needs:
```python
@dataclass
class FileEditResult(FileOperationResult):
    # Base fields
    title: str
    filepath: str
    exists: bool
    operation: str = "edit"
    metadata: Dict[str, Any] = None

    # Diff-specific fields
    original_content: Optional[str] = None
    new_content: Optional[str] = None
    diff: Optional[str] = None
    changes: Optional[Dict[str, int]] = None  # {"insertions": 5, "deletions": 3}

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def calculate_diff(self):
        """Generate unified diff from content."""
        if self.original_content and self.new_content:
            import difflib
            self.diff = ''.join(difflib.unified_diff(
                self.original_content.splitlines(keepends=True),
                self.new_content.splitlines(keepends=True),
                fromfile=f"a/{self.filepath}",
                tofile=f"b/{self.filepath}"
            ))

            # Count changes
            self.changes = {
                "insertions": self.diff.count("+") if self.diff else 0,
                "deletions": self.diff.count("-") if self.diff else 0
            }
```

## Integration Plan for Diff Display

### 1. Update update_file to Return Structured Data
```python
@file_tool
async def update_file(filepath: str, target: str, patch: str) -> FileEditResult:
    # ... existing logic to read original and apply patch ...

    result = FileEditResult(
        title=os.path.relpath(filepath, os.getcwd()),
        filepath=filepath,
        exists=True,
        operation="update",
        original_content=original,
        new_content=new_content
    )
    result.calculate_diff()

    return result
```

### 2. Update UI Renderer to Handle Structured Results
```python
# In panels.py
def render_file_edit_result(result: FileEditResult) -> "Widget":
    """Render a structured file edit result with diff display."""
    if result.diff:
        return DiffDisplayWidget(
            diff=result.diff,
            title=result.title,
            changes=result.changes
        )
    return create_simple_result_panel(result.to_display_string())
```

### 3. Create Diff Display Widget
```python
from rich.console import Console
from rich.syntax import Syntax

class DiffDisplayWidget:
    def __init__(self, diff: str, title: str, changes: Dict[str, int]):
        self.diff = diff
        self.title = title
        self.changes = changes

    def __rich_console__(self, console: Console, options):
        """Render diff with syntax highlighting."""
        # Header with file and change summary
        header = f"[bold]{self.title}[/bold] "
        if self.changes:
            header += f"[green]+{self.changes['insertions']}[/green] "
            header += f"[red]-{self.changes['deletions']}[/red]"

        yield Text(header)

        # Syntax-highlighted diff
        yield Syntax(
            self.diff,
            lexer="diff",
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )
```

## Summary of Key Insights

1. **Structured Returns**: TypeScript's pattern of returning rich objects instead of strings enables better UI integration
2. **Metadata Tracking**: Including file state, operation type, and diagnostics in the return value
3. **Event Systems**: The TypeScript version uses events for file change tracking, enabling reactive UI updates
4. **Permission Flow**: Pre-operation permission checks provide better security and user control
5. **LSP Integration**: Built-in language server support provides immediate feedback on file changes

For the Python diff display implementation, adopting the structured return pattern is most critical. It separates the data from presentation, allowing the UI to decide how to display changes while keeping the tool logic simple.