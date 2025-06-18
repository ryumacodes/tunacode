# Characterization Test Plan for TunaCode

## Overview
This document outlines the remaining characterization tests needed to capture the current behavior of the TunaCode codebase. The goal is to achieve ~80% code coverage with golden-master tests that preserve existing behavior during refactoring.

## Completed Tests ✓
1. **File Operation Tools** (tests/test_characterization_*.py)
   - `test_characterization_read_file.py` - ReadFileTool behavior
   - `test_characterization_write_file.py` - WriteFileTool behavior
   - `test_characterization_update_file.py` - UpdateFileTool behavior
   - `test_characterization_bash.py` - BashTool behavior

## Remaining Tests to Implement

### 1. Core Tool Tests

#### A. GrepTool (`/home/tuna/tunacode/tests/test_characterization_grep.py`)
- **Location**: `src/tunacode/tools/grep.py`
- **Key behaviors to capture**:
  - Fast-glob prefiltering with MAX_GLOB limit
  - Three search strategies (python, ripgrep, hybrid)
  - 3-second deadline for first match
  - TooBroadPatternError behavior
  - File pattern expansion ({py,js,ts} syntax)
  - Context lines handling
  - Binary file skipping
  - Large repository performance

#### B. ListDirTool (`/home/tuna/tunacode/tests/test_characterization_list_dir.py`)
- **Location**: `src/tunacode/tools/list_dir.py`
- **Key behaviors to capture**:
  - Directory sorting (dirs first, then files)
  - Type indicators (/, *, @, ?)
  - Hidden file filtering
  - Max entries limit
  - Permission errors
  - Symlink handling
  - Non-existent directory errors

#### C. RunCommandTool (`/home/tuna/tunacode/tests/test_characterization_run_command.py`)
- **Location**: `src/tunacode/tools/run_command.py`
- **Key behaviors to capture**:
  - Command execution (if different from bash)
  - Error handling
  - Output formatting

### 2. Agent System Tests

#### A. Main Agent (`/home/tuna/tunacode/tests/test_characterization_agent.py`)
- **Location**: `src/tunacode/core/agents/main.py`
- **Key functions**:
  - `get_or_create_agent()` - Lazy agent creation
  - `process_request()` - Main processing loop
  - `patch_tool_messages()` - Orphaned tool handling
  - `extract_and_execute_tool_calls()` - Fallback tool parsing
- **Key behaviors**:
  - Max iterations handling
  - Tool registration with retries
  - System prompt loading
  - Files in context tracking
  - Thought display mode
  - Iteration counting
  - Fallback response generation

### 3. State Management Tests

#### A. StateManager (`/home/tuna/tunacode/tests/test_characterization_state.py`)
- **Location**: `src/tunacode/core/state.py`
- **Key behaviors**:
  - Session state initialization
  - Message history management
  - Agent caching by model
  - Cost tracking
  - Tool call history
  - Files in context set
  - State reset functionality
  - Yolo mode toggling

### 4. Command System Tests

#### A. CommandRegistry (`/home/tuna/tunacode/tests/test_characterization_command_registry.py`)
- **Location**: `src/tunacode/cli/commands.py`
- **Key behaviors**:
  - Command discovery
  - Partial command matching
  - Ambiguous command handling
  - Command categories
  - Unknown command errors
  - Command execution flow

#### B. Individual Commands (`/home/tuna/tunacode/tests/test_characterization_commands.py`)
- **Key commands to test**:
  - `YoloCommand` - Permission toggling
  - `ClearCommand` - Message clearing & orphan patching
  - `ModelCommand` - Model switching & validation
  - `IterationsCommand` - Iteration limit setting (1-50)
  - `CompactCommand` - History summarization
  - `HelpCommand` - Help display
  - `ExitCommand` - Exit behavior
  - `BranchCommand` - Git branch creation
  - `UndoCommand` - Message removal

### 5. Tool Handler Tests

#### A. ToolHandler (`/home/tuna/tunacode/tests/test_characterization_tool_handler.py`)
- **Location**: `src/tunacode/core/tool_handler.py`
- **Key behaviors**:
  - Confirmation checking (yolo mode)
  - Tool ignore list management
  - Confirmation response processing
  - "Skip future" functionality

### 6. Setup System Tests

#### A. SetupCoordinator (`/home/tuna/tunacode/tests/test_characterization_setup.py`)
- **Location**: `src/tunacode/core/setup/coordinator.py`
- **Key behaviors**:
  - Step execution order
  - Validation flow
  - Error handling
  - State initialization

#### B. Individual Setup Steps
- **EnvironmentSetup** - API key detection
- **ModelSetup** - Model validation
- **ConfigSetup** - User config loading/creation
- **GitSafetySetup** - Git status checking

### 7. UI Component Tests

#### A. REPL (`/home/tuna/tunacode/tests/test_characterization_repl.py`)
- **Location**: `src/tunacode/cli/repl.py`
- **Key behaviors**:
  - Multiline input handling
  - Command detection
  - Syntax highlighting
  - Exit conditions
  - Error display

#### B. Tool UI (`/home/tuna/tunacode/tests/test_characterization_tool_ui.py`)
- **Location**: `src/tunacode/ui/tool_ui.py`
- **Key behaviors**:
  - Confirmation prompts
  - Diff display for file operations
  - Permission responses
  - UI formatting

### 8. Utility Tests

#### A. BM25 Search (`/home/tuna/tunacode/tests/test_characterization_bm25.py`)
- **Location**: `src/tunacode/utils/bm25.py`
- **Key behaviors**:
  - Document indexing
  - Query scoring
  - Result ranking

#### B. Diff Utils (`/home/tuna/tunacode/tests/test_characterization_diff.py`)
- **Location**: `src/tunacode/utils/diff_utils.py`
- **Key behaviors**:
  - Unified diff generation
  - Color formatting
  - Line number handling

#### C. Token Counter (`/home/tuna/tunacode/tests/test_characterization_tokens.py`)
- **Location**: `src/tunacode/utils/token_counter.py`
- **Key behaviors**:
  - Token counting by model
  - Cost calculation
  - Message token estimation

## Test Implementation Guidelines

1. **Golden Master Approach**:
   - Capture EXACT current behavior
   - Include edge cases and quirks
   - Don't fix bugs, just document them

2. **Test Structure**:
   ```python
   async def test_behavior_name(self):
       """Capture behavior when [scenario]."""
       # Arrange
       setup_test_data()
       
       # Act
       result = await function_under_test()
       
       # Assert - Golden master
       assert result == expected_current_behavior
   ```

3. **Common Patterns**:
   - Use `pytest.mark.asyncio` for async tests
   - Mock external dependencies
   - Create temp directories for file operations
   - Capture both success and error paths
   - Test boundary conditions

4. **Coverage Goals**:
   - Focus on critical paths first
   - Aim for 80% coverage overall
   - 100% coverage for core business logic
   - Skip UI rendering code if needed

## Execution Order

1. **High Priority** (Complete first):
   - GrepTool - Complex search logic
   - Main Agent - Core processing loop
   - StateManager - Central state tracking
   - CommandRegistry - Command routing

2. **Medium Priority**:
   - ListDirTool - Simple but important
   - Individual Commands - User interactions
   - ToolHandler - Confirmation logic
   - SetupCoordinator - Initial setup

3. **Low Priority** (If time permits):
   - UI Components - Less critical
   - Utility functions - Well isolated
   - Individual setup steps

## Success Metrics

- [ ] All core tools have characterization tests
- [ ] Agent system behavior is captured
- [ ] Command system is fully tested
- [ ] State management is covered
- [ ] ~80% overall code coverage achieved
- [ ] Tests pass without modifying source code
- [ ] Refactoring can proceed safely