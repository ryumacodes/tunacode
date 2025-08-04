# Python File Refactoring Plan - Progress Tracker

## Overview
This document tracks the refactoring progress for reducing large Python files in the TunaCode project to improve maintainability and readability.

### Target Files
- ✅ `./src/tunacode/tools/grep.py` (694 lines)
- ✅ `./src/tunacode/cli/repl.py` (578 lines)  
- ✅ `./src/tunacode/core/agents/main.py` (1613 lines)

## Completed Work

### ✅ Phase 1: Characterization Testing (COMPLETED)

#### grep.py Testing
- **Status**: ✅ Complete
- **Test File**: `tests/characterization/test_characterization_grep.py`
- **Tests Created**: 15 tests
- **Coverage**:
  - Basic pattern searching
  - Case-sensitive/insensitive search
  - File type filtering
  - Glob pattern filtering
  - Regex mode
  - Context lines
  - Output modes
  - Exclusion patterns
  - Multiline mode
  - Result limiting
  - Parallel execution
  - Error handling
- **Commit**: `07fddb1` - "test: add characterization tests for grep.py refactoring"

#### repl.py Testing
- **Status**: ✅ Complete (with some tests needing refinement)
- **Test File**: `tests/characterization/test_characterization_repl.py`
- **Tests Created**: 19 tests
- **Coverage**:
  - Argument parsing
  - Tool handler operations
  - Command handling (shell, registry, invalid)
  - Request processing
  - Error handling
  - REPL interaction loop
  - Keyboard interrupt handling
  - Agent busy state
  - Output display (streaming/non-streaming)
  - Tool recovery mechanisms
- **Commit**: `fa16235` - "test: add characterization tests for repl.py refactoring (partial)"
- **Note**: 8 tests need fixing due to mock setup issues

#### main.py Testing
- **Status**: ✅ Complete
- **Test File**: `tests/characterization/test_characterization_main.py`
- **Tests Created**: 16 tests (all passing)
- **Coverage**:
  - Task completion detection
  - Tool buffer operations
  - Parallel tool execution
  - JSON tool call parsing
  - Tool call extraction from text
  - Message patching for orphaned tools
  - Agent creation and caching
- **Commit**: `e51d11c` - "test: add characterization tests for main.py refactoring"

### ✅ Phase 2: Create Rollback Points (COMPLETED)
- **Status**: ✅ Complete
- **Rollback Commit**: `7b4f31e` - "chore: create rollback point before refactoring grep.py, repl.py, and main.py"
- **Description**: Full project snapshot before any refactoring changes

## Remaining Work

### ✅ Phase 3: Dead Code Removal (COMPLETED)

#### Tasks:
1. **Analyze each file for dead code**:
   - [x] Unused imports
   - [x] Unreferenced functions/methods
   - [x] Unreachable code paths
   - [x] Deprecated/commented code blocks

2. **Remove dead code while ensuring tests pass**:
   - [x] grep.py dead code removal (removed duplicate 'node_modules' entry)
   - [x] repl.py dead code removal (no dead code found)
   - [x] main.py dead code removal (no dead code found)

3. **Commit**: ✅ `44e444d` - `refactor: remove dead code from grep.py`

### 🔄 Phase 4: File Decomposition (IN PROGRESS)

#### ✅ grep.py Decomposition (694 → 435 lines) - COMPLETED
- [x] Created `grep_components/` package
- [x] Extract `search_result.py` - Data classes (34 lines)
- [x] Extract `pattern_matcher.py` - Pattern matching logic (149 lines)
- [x] Extract `file_filter.py` - File filtering logic (90 lines)
- [x] Extract `result_formatter.py` - Output formatting (46 lines)
- [x] Keep search orchestration in `grep.py` (435 lines)
- **Commit**: `32cb16a` - `refactor: decompose grep.py into smaller modules`

#### repl.py Decomposition Plan (578 → <400 lines each)
- [ ] Extract `command_parser.py` - Command parsing logic
- [ ] Extract `input_handler.py` - Input handling
- [ ] Extract `output_formatter.py` - Output formatting
- [ ] Keep main REPL loop in `repl.py`

#### main.py Decomposition Plan (1613 → <400 lines each)
- [ ] Extract `tools/` subdirectory for tool definitions
- [ ] Extract `agent_config.py` - Agent configuration
- [ ] Extract `message_handler.py` - Message handling
- [ ] Extract `response_processor.py` - Response processing logic
- [ ] Extract `tool_executor.py` - Tool execution and parallelization
- [ ] Keep core agent logic in `main.py`

### 🔄 Phase 5: Apply Modern Python Standards (PENDING)

#### Standards to Apply:
1. **Type hints throughout**:
   - [ ] Add type hints to all public methods
   - [ ] Use proper return type annotations
   - [ ] Import from `typing` for complex types

2. **Dataclasses for data structures**:
   - [ ] Convert existing data classes
   - [ ] Use `@dataclass` decorator
   - [ ] Add field types and defaults

3. **Pathlib instead of os.path**:
   - [ ] Replace `os.path` operations
   - [ ] Use `Path` objects consistently
   - [ ] Update file operations

4. **Context managers for resources**:
   - [ ] Use `with` statements for file operations
   - [ ] Implement custom context managers where needed

5. **Enum for constants**:
   - [ ] Replace string constants with Enums
   - [ ] Group related constants

## Validation Checklist

After each phase, ensure:
- [ ] All characterization tests pass
- [ ] No public API changes (unless explicitly needed)
- [ ] Each new file is under 500 lines
- [ ] Imports are organized (stdlib → third-party → local)
- [ ] Type hints added for all public methods
- [ ] Docstrings present for modules, classes, and public methods
- [ ] No circular imports introduced
- [ ] Performance characteristics maintained

## Risk Mitigation

1. **Rollback Strategy**: 
   - Rollback point created at commit `7b4f31e`
   - Can revert with: `git reset --hard 7b4f31e`

2. **Test Safety Net**:
   - Characterization tests ensure behavior preservation
   - Run tests after each change: `pytest tests/characterization/`

3. **Incremental Approach**:
   - Small, focused commits
   - One file at a time
   - Test continuously

## Next Steps

1. ✅ Phase 3 Complete: Dead code removal
   - Removed duplicate entry from grep.py
   - No dead code found in repl.py or main.py
   - Fixed unused imports in test files

2. Begin Phase 4: File decomposition
   - Start with grep.py decomposition
   - Fix failing repl.py tests before refactoring
   - Consider adding performance benchmarks

3. Track progress through remaining phases

## Commands Reference

```bash
# Run all characterization tests
pytest tests/characterization/ -v

# Run tests for specific module
pytest tests/characterization/test_characterization_grep.py -v

# Check line counts
wc -l src/tunacode/tools/grep.py src/tunacode/cli/repl.py src/tunacode/core/agents/main.py

# Run linting
make lint

# Run with coverage
pytest tests/characterization/ --cov=tunacode --cov-report=html
```

## Success Metrics

- All files under 500 lines
- All characterization tests passing
- No performance regression
- Improved code organization and readability
- Type safety through annotations
- Modern Python idioms applied

---
*Last Updated: Phase 3 Complete, grep.py Decomposition Complete - Ready to continue Phase 4 with repl.py*