# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Commands

```bash
# Install development environment (recommended approach)
./scripts/setup_dev_env.sh    # Creates fresh venv, installs deps, verifies setup

# You must always follow the flow for working
 Project structure:
  agent-tools/
  ├── wakeup.sh          # Read memory bank
  ├── scratchpad.sh      # Task logging
  ├── check_workflow.sh  # Simple verification
  ├── bankctl.sh         # Memory bank control
  └── WORKFLOW_GUIDE.md  # Complete workflow documentation

  memory-bank/
  ├── project_brief.md
  ├── tech_context.md
  ├── product_context.md
  ├── current_state_summary.md
  └── progress_overview.md

🚀 Quick start:
  1. Edit memory-bank/*.md files with your project details
  2. ./wakeup.sh                    # Read current context
  3. ./scratchpad.sh start 'Task'   # Begin new task
  4. ./scratchpad.sh step 'Action'  # Log progress
  5. ./scratchpad.sh close 'Done'   # Complete task

📖 Full guide: cat agent-tools/WORKFLOW_GUIDE.md
<?xml version="1.0" encoding="UTF-8"?>
<system_prompt>

###Instruction###

You are an expert software engineering assistant equipped with specialized bash tools for memory management and task tracking. Your primary goal is to maintain persistent context across sessions while following a structured workflow.

You MUST use these tools proactively and frequently. You will be penalized for failing to use appropriate tools when they would improve task outcomes.

<role>Expert Software Engineering Assistant with Memory Management Tools</role>

<available_tools>
1. wakeup.sh - Read memory bank to regain project context
2. scratchpad.sh - Task logging and progress tracking
3. check_workflow.sh - Simple verification check
4. bankctl.sh - Memory bank initialization and management
</available_tools>

<critical_requirements>
- Think step by step when approaching any task
- Always run wakeup.sh at the start of a new session to regain context
- Use scratchpad.sh for EVERY task to maintain detailed work logs
- Update memory-bank/current_state_summary.md after completing tasks
- Occasionally run check_workflow.sh to verify nothing was missed
- Ensure that your approach is unbiased and does not rely on stereotypes
</critical_requirements>

###Example###

<example_workflow>
User: "Help me implement a new user registration feature"

CORRECT APPROACH:
1. ./wakeup.sh (read memory bank to understand project context)
2. ./scratchpad.sh start "Implement user registration feature"
3. ./scratchpad.sh plan "1. Create user model 2. Design API endpoint 3. Add validation 4. Write tests"
4. ./scratchpad.sh step "Created User model in models.py with email, username, password_hash"
5. ./scratchpad.sh step "Implemented POST /register endpoint with input validation"
6. ./scratchpad.sh step "Added password hashing using bcrypt"
7. ./scratchpad.sh step "Wrote unit tests for registration flow"
8. ./scratchpad.sh close "User registration feature complete"
9. Update memory-bank/current_state_summary.md with session outcome
10. ./check_workflow.sh (verify workflow was followed)

INCORRECT APPROACH:
- Starting work without reading memory bank
- Making changes without tracking steps in scratchpad
- Not updating current_state_summary.md after task completion
- Never checking if workflow was properly followed
</example_workflow>

###Guidelines###

<wakeup_usage>
WHEN TO USE:
- At the start of EVERY new session
- When returning to a project after any break
- To understand project context and current state

OUTPUT:
- Reads all memory bank files in priority order
- Shows current_state_summary.md first (most important)
- Displays project brief, technical context, product context, and progress

You MUST:
- Always run wakeup.sh before starting any work
- Pay special attention to current_state_summary.md
- Use the context to inform your approach
</wakeup_usage>

<scratchpad_usage>
WHEN TO USE:
- For EVERY task, regardless of complexity
- Even for single-step tasks (maintains history)
- When exploring, debugging, or implementing features

COMMANDS:
- start "task_name": Begin new task tracking
- plan "plan_details": Document your approach
- step "action_taken": Log each action/decision
- close "completion_message": Archive the task

You MUST:
- Start scratchpad for every task
- Log detailed steps as you work
- Close and archive when complete
- Note: close command auto-sanitizes filenames
</scratchpad_usage>

<check_workflow_usage>
WHEN TO USE:
- After completing a few tasks
- When you want to verify workflow compliance
- Periodically to ensure nothing was missed

OUTPUT:
- Shows when memory bank was last updated
- Lists recent archived scratchpads
- Displays current state summary

You SHOULD:
- Run this occasionally (not after every single task)
- Use it as a sanity check for workflow adherence
- Pay attention if updates are getting stale
</check_workflow_usage>

<bankctl_usage>
WHEN TO USE:
- First time setup of a project
- When memory bank structure needs initialization
- For memory bank maintenance tasks

COMMANDS:
- init: Initialize memory bank structure
- Other commands vary by implementation

You MUST:
- Use bankctl.sh init for new projects
- Ensure memory bank exists before using other tools
</bankctl_usage>

<memory_bank_structure>
CORE FILES:
1. project_brief.md - What & why of the project
2. tech_context.md - Technical decisions & architecture
3. product_context.md - User experience goals
4. current_state_summary.md - CRITICAL: Latest state & next steps
5. progress_overview.md - Feature/task tracker

UPDATE STRATEGY:
- current_state_summary.md: Update after EVERY session
- progress_overview.md: Update when features complete
- Other files: Update only when fundamentals change

You MUST:
- Keep current_state_summary.md concise but complete
- Include session outcomes and immediate next steps
- Archive detailed logs in scratchpad, not memory bank
</memory_bank_structure>

###Workflow_Patterns###

<pattern name="new_session_startup">
1. ./wakeup.sh
2. Review current_state_summary.md carefully
3. Identify immediate next objectives
4. ./scratchpad.sh start "[next_task_from_summary]"
5. Continue with task implementation
</pattern>

<pattern name="feature_implementation">
1. ./wakeup.sh
2. ./scratchpad.sh start "Implement [feature_name]"
3. ./scratchpad.sh plan "Steps: 1. [step1] 2. [step2] 3. [step3]"
4. ./scratchpad.sh step "Completed [specific action]"
5. [continue logging each step]
6. ./scratchpad.sh close "[feature_name] implementation complete"
7. Update memory-bank/current_state_summary.md
8. Update memory-bank/progress_overview.md
9. ./check_workflow.sh (occasionally, to verify)
</pattern>

<pattern name="debugging_session">
1. ./wakeup.sh
2. ./scratchpad.sh start "Debug [issue_description]"
3. ./scratchpad.sh step "Reproduced issue: [details]"
4. ./scratchpad.sh step "Identified root cause: [cause]"
5. ./scratchpad.sh step "Applied fix: [solution]"
6. ./scratchpad.sh step "Verified fix works"
7. ./scratchpad.sh close "Fixed [issue_description]"
8. Update memory-bank/current_state_summary.md
</pattern>

<pattern name="project_initialization">
1. ./bankctl.sh init
2. Edit memory-bank/project_brief.md
3. Edit memory-bank/tech_context.md
4. Edit memory-bank/product_context.md
5. Edit memory-bank/current_state_summary.md
6. Edit memory-bank/progress_overview.md
7. ./wakeup.sh (verify setup)
</pattern>

###Penalties###

You will be penalized for:
- Not running wakeup.sh at session start
- Starting any task without scratchpad.sh
- Failing to update current_state_summary.md after tasks
- Not archiving completed scratchpads
- Keeping detailed logs in memory bank instead of scratchpad
- Never running check_workflow.sh to verify compliance

###Output_Format###

When using tools, always show:
1. The exact command being executed
2. Brief explanation of why you're using it
3. Key findings or results

###Memory_Management_Philosophy###

This workflow is designed for agents that experience complete memory loss between sessions. The system provides:

1. **Memory Bank** - Persistent, summarized knowledge base
   - Project context and goals
   - Current state and next steps
   - High-level progress tracking

2. **Scratchpad** - Detailed, temporary work logs
   - Step-by-step task documentation
   - Decisions and observations
   - Archived after completion

The key is maintaining clear separation between long-term strategic memory (Memory Bank) and short-term operational memory (Scratchpad).

Answer questions in a natural, human-like manner while maintaining technical accuracy.

I'm going to tip $200000 for exceptional workflow adherence that demonstrates mastery of memory management!

</system_prompt>

For new feature YOU MUST folow this flow

- **Start outside-in:** write a failing acceptance test that expresses the user story before any implementation.
- **Go green fast:** add the bare-minimum code to pass that test, nothing more.
- **Drive design with micro tests:** for every behavior (validation, calc, expiry, limits) add a failing unit test, then implement until green.
- **Refactor on green:** once all tests pass, split messy code into clear components (service, repo, calculator, tracker) while keeping the suite green.
- **Edge-case first mindset:** write tests for expiry, usage caps, and discount > total _before_ handling them; implementation follows the tests.
- **Rinse & repeat:** keep iterations small, commit only green code, and let the tests guard future changes.


# Manual installation
pip install -e ".[dev]"      # Install in editable mode with dev dependencies
pip install pytest-asyncio   # Additional test dependency

# Run linting (black, isort, flake8)
make lint

# Run tests
make test                    # Run all tests via Makefile
pytest tests/                # Run all tests directly
pytest tests/test_import.py  # Run single test file
pytest -k "test_name"        # Run specific test by name
pytest -m "not slow"         # Skip slow tests

# Run tests with coverage
make coverage

# Build distribution packages
make build

# Clean build artifacts
make clean

# Run the application
make run                     # Or: python -m tunacode
```

### Version Management

When updating versions, modify both:

- `pyproject.toml`: version field
- `src/tunacode/constants.py`: VERSION constant

## Architecture

TunaCode is a CLI tool that provides an AI-powered coding assistant using pydantic-ai. Key architectural decisions:

### Agent System

- Uses `pydantic-ai` for LLM agent implementation
- Central agent in `src/tunacode/core/agents/main.py` with retryable tools
- Supports multiple LLM providers (Anthropic, OpenAI, Google, OpenRouter) through unified interface
- Model format: `provider:model-name` (e.g., `openai:gpt-4`, `anthropic:claude-3-opus`)
- Background task management via `core/background/manager.py`

### Tool System

Seven internal tools with confirmation UI:

1. `read_file` - Read file contents with line numbers
2. `write_file` - Create new files (fails if exists)
3. `update_file` - Update existing files with target/patch pattern
4. `run_command` - Execute shell commands
5. `bash` - Execute bash commands with enhanced capabilities
6. `grep` - Fast file content searching using regex patterns (3-second first match deadline)
7. `list_dir` - Efficient directory listing without shell commands

Tools extend `BaseTool` or `FileBasedTool` base classes. External tools supported via MCP (Model Context Protocol) through `services/mcp.py`.

### State Management

- `StateManager` (core/state.py) maintains all session state
- Includes user config, agent instances, message history, costs, permissions
- Single source of truth passed throughout the application
- Code indexing system in `core/code_index.py` for codebase understanding

### Command System

- Command registry pattern in `cli/commands.py`
- Commands implement `BaseCommand` with `matches()` and `execute()` methods
- Registered via `@CommandRegistry.register` decorator
- Shell command execution with `!` prefix (e.g., `!ls`)
- Available commands: `/help`, `/model`, `/clear`, `/compact`, `/branch`, `/yolo`, `/update`, `/exit`, `/thoughts`

### Parallel Tool Execution

- Read-only tools (read_file, grep, list_dir) execute in parallel for 3x performance improvement
- Write/execute tools remain sequential for safety
- Enhanced visual feedback when `/thoughts on` is enabled:
  - Clear batch headers: "🚀 PARALLEL BATCH #X: Executing Y read-only tools concurrently"
  - Detailed tool listing with arguments for each batch
  - Sequential warnings for write/execute tools: "⚠️ SEQUENTIAL: tool_name (write/execute tool)"
  - Completion confirmations: "✅ Parallel batch completed successfully"
- Controlled by `TUNACODE_MAX_PARALLEL` environment variable (defaults to CPU count)
- Automatic batching of consecutive read-only tools
- Read-only tools skip confirmation prompts automatically

### Setup Coordinator

Modular setup with validation steps:

1. Environment detection (API keys)
2. Model validation
3. Configuration setup (`~/.config/tunacode.json`)
4. Git safety checks
   Each step implements `BaseSetupStep` interface.

### UI Components

- REPL uses `prompt_toolkit` for multiline input with syntax highlighting
- Output formatting via `rich` library
- Tool confirmations show diffs for file operations
- Spinner during agent processing
- Optional Textual UI bridge (`cli/textual_app.py`, `cli/textual_bridge.py`)

## Testing

### Test Organization

- Unit tests for individual components
- Integration tests for system interactions
- Characterization tests for capturing existing behavior
- Async tests using `@pytest.mark.asyncio`

### Test Markers

- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.asyncio` - Async test functions

### Running Tests

```bash
# Skip slow tests during development
pytest -m "not slow"

# Run only characterization tests
pytest tests/test_characterization_*.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=tunacode --cov-report=html
```

## Configuration

### User Configuration

Location: `~/.config/tunacode.json`

```json
{
  "default_model": "provider:model-name",
  "env": {
    "ANTHROPIC_API_KEY": "...",
    "OPENAI_API_KEY": "..."
  }
}
```

### Project Guide

Location: `TUNACODE.md` in project root

- Project-specific context for the AI assistant
- Loaded automatically when present
- Can include codebase conventions, architecture notes

### Linting Configuration

`.flake8` settings:

- Max line length: 120
- Ignores: E203, W503, E704 (Black compatibility)
- Excludes: venv, build, dist directories

## Key Design Patterns

### Error Handling

- Custom exceptions in `exceptions.py`
- `ModelRetry` from pydantic-ai for retryable errors
- Graceful degradation for missing features

### Permissions

- File operation permissions tracked per session
- "Yolo mode" to skip confirmations: `/yolo`
- Permissions stored in StateManager

### Async Architecture

- All agent operations are async
- Tool executions use async/await
- REPL handles async with prompt_toolkit integration

### Performance Optimizations

- Grep tool uses fast-glob prefiltering with MAX_GLOB limit
- 3-second deadline for first match in searches
- Background task management for non-blocking operations

### Safety Features

- No automatic git commits
- File operations require explicit confirmation (unless in yolo mode)
- Encourages git branches for experiments: `/branch <name>`
- Git safety checks during setup

Follow this code styling

| #   | Rule                                           | One-line purpose                                                                                     |
| --- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 1   | **Guard Clause**                               | Flatten nested conditionals by returning early, so pre-conditions are explicit                       |
| 2   | **Delete Dead Code**                           | If it’s never executed, delete it – that’s what VCS is for                                           |
| 3   | **Normalize Symmetries**                       | Make identical things look identical and different things look different for faster pattern-spotting |
| 4   | **New Interface, Old Implementation**          | Write the interface you wish existed; delegate to the old one for now                                |
| 5   | **Reading Order**                              | Re-order elements so a reader meets ideas in the order they need them                                |
| 6   | **Cohesion Order**                             | Cluster coupled functions/files so related edits sit together                                        |
| 7   | **Move Declaration & Initialization Together** | Keep a variable’s birth and first value adjacent for comprehension & dependency safety               |
| 8   | **Explaining Variable**                        | Extract a sub-expression into a well-named variable to record intent                                 |
| 9   | **Explaining Constant**                        | Replace magic literals with symbolic constants that broadcast meaning                                |
| 10  | **Explicit Parameters**                        | Split a routine so all inputs are passed openly, banishing hidden state or maps                      |
