# Characterization Test Plan for Agent Abilities

This document outlines a plan for creating a suite of characterization tests for the agent's core abilities. These tests will capture the agent's current behavior, providing a safety net for future refactoring and bug fixing.

## 1. Core Agent Logic and File Locations

The agent's core logic is distributed across several key files:

- **Agent Entrypoint:** [`src/tunacode/core/agents/main.py`](src/tunacode/core/agents/main.py) - This is the main entry point for the agent, responsible for orchestrating the entire process of receiving a request, selecting a tool, and executing it.
- **Tool Handling:** [`src/tunacode/core/tool_handler.py`](src/tunacode/core/tool_handler.py) - This module is responsible for managing the available tools, including their loading, validation, and execution.
- **Tool Implementations:** [`src/tunacode/tools/`](src/tunacode/tools/) - This directory contains the individual tool implementations, such as `read_file`, `write_file`, `grep`, etc. Each file in this directory corresponds to a specific agent ability.
- **Command Line Interface:** [`src/tunacode/cli/`](src/tunacode/cli/) - This directory contains the CLI for interacting with the agent.

## 2. Phased Characterization Test Plan

We will implement the characterization tests in a phased approach, starting with the most fundamental and high-impact abilities.

### Test Organization

**Important:** All new characterization tests should be created within a dedicated directory, such as `tests/characterization/`, to maintain a clean and organized codebase. This helps separate characterization tests from other test types and makes it easier to manage and run specific test suites.

### Phase 1: Core File Operations

This phase focuses on the agent's ability to interact with the file system. These are the most critical functions and are directly related to the observed test failures in `tests/crud/test_core_file_operations.py`.

- **`read_file`:**
  - Test reading a whole file.
  - Test reading a file with line numbers.
  - Test reading a non-existent file.
  - Test reading an empty file.
- **`write_file`:**
  - Test creating a new file.
  - Test overwriting an existing file.
  - Test creating a file in a nested directory.
- **`update_file`:**
  - Test a simple replacement.
  - Test a multi-line replacement.
  - Test that indentation is preserved.
- **`list_dir`:**
  - Test listing files in the current directory.
  - Test listing files recursively.
  - Test listing files in a subdirectory.

### Phase 2: Search and Navigation

This phase focuses on the agent's ability to find information within the workspace.

- **`grep`:**
  - Test a simple string search.
  - Test a regex search.
  - Test searching with file patterns.
  - Test case-sensitive and case-insensitive search.
- **`glob`:**
  - Test a simple glob pattern.
  - Test a recursive glob pattern.

### Phase 3: Command Execution

This phase focuses on the agent's ability to execute shell commands.

- **`bash` / `run_command`:**
  - Test a simple command (e.g., `ls`).
  - Test a command with arguments.
  - Test a command that produces a non-zero exit code.

## 3. Addressing Existing Test Failures

The existing test failures in [`tests/crud/test_core_file_operations.py`](tests/crud/test_core_file_operations.py) indicate potential instability in the underlying file operation tools. The characterization tests will help in the following ways:

1.  **Isolate Failures:** By testing the agent's abilities at a higher level, we can determine if the failures are in the tool's implementation or in the agent's use of the tool.
2.  **Provide a Safety Net:** Once we have a comprehensive suite of characterization tests, we can refactor the underlying tool implementations with confidence, knowing that the tests will catch any regressions in the agent's behavior.
3.  **Clarify Expected Behavior:** The characterization tests will serve as executable documentation of the agent's expected behavior, which is crucial for long-term maintenance and development.

This plan provides a clear path forward for improving the reliability and robustness of the agent.
