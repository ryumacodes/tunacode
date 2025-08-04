# Python File Refactoring Prompt - Reducing Large Files

## Task Overview

You are tasked with refactoring Python files that exceed 500 lines to improve maintainability and readability. The target files are:
- `./src/tunacode/tools/grep.py` (694 lines)
- `./src/tunacode/cli/repl.py` (578 lines)  
- `./src/tunacode/core/agents/main.py` (1613 lines)

## Workflow Requirements

Follow this exact sequence for each file:

### Phase 1: Characterization Testing
1. **Analyze the current file** to understand its public API and key behaviors
2. **Write characterization tests** in `tests/characterization/test_characterization_[module].py` that capture:
   - All public methods and their current behavior
   - Key integration points
   - Edge cases currently handled
   - Expected outputs for typical inputs
3. **Run the tests** to ensure they pass with the current implementation
4. **Commit these tests** with message: `test: add characterization tests for [module] refactoring`

### Phase 2: Create Rollback Point
```bash
git add -A
git commit -m "chore: create rollback point before refactoring [module]" --no-verify
```

### Phase 3: Dead Code Removal
1. **Identify unused code** by checking for:
   - Unused imports
   - Unreferenced functions/methods
   - Unreachable code paths
   - Deprecated/commented code blocks
2. **Remove dead code** while ensuring all characterization tests still pass
3. **Commit** with message: `refactor: remove dead code from [module]`

### Phase 4: File Decomposition
1. **Analyze cohesion** - identify logical groupings:
   - Related functionality that operates on similar data
   - Methods that call each other frequently
   - Shared responsibility areas
   
2. **Extract components** following these patterns:
   - **For grep.py**: Consider separating:
     - Pattern matching logic → `pattern_matcher.py`
     - File filtering logic → `file_filter.py`
     - Search orchestration → keep in `grep.py`
   
   - **For repl.py**: Consider separating:
     - Command parsing → `command_parser.py`
     - Input handling → `input_handler.py`
     - Output formatting → `output_formatter.py`
     - Main REPL loop → keep in `repl.py`
   
   - **For main.py**: Consider separating:
     - Tool definitions → `tools/` subdirectory
     - Agent configuration → `agent_config.py`
     - Message handling → `message_handler.py`
     - Core agent logic → keep in `main.py`

3. **Apply extraction patterns**:
   - Move related functions/classes to new modules
   - Use clear import statements
   - Maintain backward compatibility with public APIs
   - Keep files under 400 lines (leaving room for growth)

### Phase 5: Modern Python Standards
Apply these patterns during refactoring:

1. **Type hints** - Add throughout:
   ```python
   def process_results(items: List[Dict[str, Any]]) -> Optional[ProcessedData]:
   ```

2. **Dataclasses** for data structures:
   ```python
   from dataclasses import dataclass
   
   @dataclass
   class SearchResult:
       file_path: Path
       line_number: int
       content: str
       match_positions: List[Tuple[int, int]]
   ```

3. **Pathlib** instead of os.path:
   ```python
   from pathlib import Path
   
   file_path = Path(filename)
   if file_path.exists() and file_path.suffix == '.py':
   ```

4. **Context managers** for resource handling:
   ```python
   with file_path.open('r', encoding='utf-8') as f:
       content = f.read()
   ```

5. **Enum** for constants:
   ```python
   from enum import Enum, auto
   
   class SearchMode(Enum):
       EXACT = auto()
       REGEX = auto()
       FUZZY = auto()
   ```

## Validation Checklist

After each refactoring phase, ensure:
- [ ] All characterization tests pass
- [ ] No public API changes (unless explicitly needed)
- [ ] Each new file is under 500 lines
- [ ] Imports are organized (stdlib → third-party → local)
- [ ] Type hints added for all public methods
- [ ] Docstrings present for modules, classes, and public methods
- [ ] No circular imports introduced
- [ ] Performance characteristics maintained (profile if needed)

## Example Refactoring Approach

For `grep.py` specifically:

```python
# Before (in grep.py - 694 lines)
class GrepTool:
    def search_files(self, pattern, paths, ...):
        # 100 lines of mixed concerns
        
    def _filter_files(self, ...):
        # File filtering logic
        
    def _match_pattern(self, ...):
        # Pattern matching logic

# After:
# grep.py (< 200 lines)
from .pattern_matcher import PatternMatcher
from .file_filter import FileFilter

class GrepTool:
    def __init__(self):
        self.matcher = PatternMatcher()
        self.filter = FileFilter()
    
    def search_files(self, pattern: str, paths: List[Path], ...) -> List[SearchResult]:
        # Orchestration only

# pattern_matcher.py (< 200 lines)
class PatternMatcher:
    # Focused pattern matching logic

# file_filter.py (< 200 lines)  
class FileFilter:
    # Focused file filtering logic
```

## Critical Rules

1. **Never break existing functionality** - characterization tests are your safety net
2. **Commit frequently** - small, focused commits for easy rollback
3. **Preserve performance** - refactoring shouldn't make code slower
4. **Maintain readability** - code should be easier to understand after refactoring
5. **Document significant changes** - update docstrings when behavior changes
