# Summary of CLAUDE.md for Next Agent

## Documentation
- Update documents in @documentation and .claude after any update.
- Use subagent `tech-docs-maintainer` for doc updates; instruct it to keep updates short and distilled.
- Follow best practices for git commits and GitHub CLI workflows.
- Commit changes frequently.
- Prioritize safety and consult user if in doubt.

## Python Coding Standards
- Always use a virtual environment (venv).
- Use type hints (PEP 484) for all function signatures.
- Prefer f-strings (PEP 498) for string formatting.
- Use `pathlib.Path` over `os.path` for filesystem operations.
- Structure imports as stdlib → third-party → local (PEP 8).
- Use dataclasses (PEP 557) for simple data containers.
- Use context managers (`with`) for resource handling.
- Use structural pattern matching (PEP 634) for complex logic.
- Run `ruff` frequently.

## Testing
- Use `make test` command to run entire test suite.
- For new features/refactors, find or create a golden/character test baseline before coding.

## Workflow
- Make a clearly labeled git commit rollback point before any updates.
- Establish a clear objective outline before starting any coding.
- Use `scratchpad-multi.sh` during work; after completion, move the MD file to the appropriate directory.
- The MD file created must be used and updated throughout the task.
- Key logic/files must be documented in the scratchpad following the specified format.

## Scratchpad Template Example
```
# Implementing Authentication Module
_Started: 2025-08-06 10:00:00_
_Agent: default_

[1] Found auth logic in src/auth/handler.py:45
[2] Key dependencies: jwt, bcrypt, session_manager
[3] Modified login function to add rate limiting
[3~1] Fixed edge case for empty passwords
```

## Archiving Documentation
- General docs go to @documentation/
- Developer or tuna-code specific docs go to @.claude
- Organize archives by category (agent, development, etc.)
- Scratchpad files must not be placed outside these directories.

## Available Agents
1. bug-context-analyzer: Investigates bug context without suggesting fixes.
2. code-synthesis-analyzer: Analyzes recent code changes for issues.
3. documentation-synthesis-qa: Creates comprehensive docs via multi-agent orchestration.
4. expert-debugger: Uses logging and root cause analysis for debugging.
5. phased-task-processor: Breaks down markdown tasks into actionable phases.
6. prompt-engineer: Optimizes prompts using engineering principles.
7. rapid-code-synthesis-qa: Provides quick quality assessments with confidence scores.
8. tech-docs-maintainer: Updates docs in @documentation and .claude directories.
