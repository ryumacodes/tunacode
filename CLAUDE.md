### Workflow

- **CRITICAL: WORKTREE REQUIREMENT** - When user requests a worktree, you MUST:
  1. Create the worktree with `git worktree add -b branch-name ../dirname`
  2. If access is blocked, immediately ask: "I cannot access the worktree directory. Should I: a) Work in a subdirectory instead, b) Use a branch in the main directory, or c) Another solution?"
  3. NEVER proceed without a worktree if user specifically requested one

- before any updates make a git commit rollback point, clearly labeled for future agents

- the clear outline of the objective MUST be established before we begin ANY coding, do not under any circumstance begin any updates untill this is clearly understood, if you have any ambiuguity or quesiton, the user can be brought in or use best practises

- use scratchpad-multi.sh as you work, after the MD file is done being used sort it to the approate directory
- To use `llm-agent-tools/scratchpad-multi.sh`, start a task with `./llm-agent-tools/scratchpad-multi.sh --agent <name> start "Task Title"` and record updates using `step`, `revise <N>`, and `branch <N>`. When complete, run `finish` to interactively archive the scratchpad to `documentation/` and/or `.claude/` (a backup is stored under `.claude/scratchpad/shared/done_tasks/`).

- the MD file created by the bash file MUST be used for the duiration of the task you will be PUNISHED if you do not update this file as you work.

- any key logic or file's must be inlcuded here in the following format if this format is not followed you will STOP reasses, and begin again

- pre-commit hooks can NOT be skipped, you will be punished for skipping the,

```
# Implementing Authentication Module
_Started: 2025-08-06 10:00:00_
_Agent: default_

[1] Found auth logic in src/auth/handler.py:45
[2] Key dependencies: jwt, bcrypt, session_manager
[3] Modified login function to add rate limiting
[3~1] Fixed edge case for empty passwords
```

- General documentation → archive to @documentation/
- Developer/tunacode-specific → archive to @ .claude
- Organize archives by category (agent/development/ etc)
- In general the scratchpad should never go in any other dirs ececpt the two above

- if a task at hand is to big to handle as a one off use the taskmaster MCP but in general this should only be used as needed, usually it will not be needed

- grep documentation and .claude as needed BOTH of these have a README.md that ahs a direcoty map, you MUST read these before any bigger grep or context searches

- in general gather as much context as needed, unless specified by the user

- this is the most important part of this prompt: Synthesis context aggressively and heuristically AS NEEDED ONLY You can deploy the appropriate subagent for complex tasks agents list below

### Documentation

- update the documents @documentation and in .claude after any update.

- use the subagent tech-docs-maintainer to update the documentation you MUST instruct the subagent to keep doc updates short you will be PUNISHED for not telling the documentation agent to keep it to only the most distilled information

- always follow best practices with git commits naming and gh cli workflows

- commit frequently

- always be on the side of safety, if you have any question consult the user

### Python Coding Standards

- always use the venv
- Use type hints (PEP 484) for all function signatures
- Prefer f-strings (PEP 498) over %-formatting or .format()
- Use pathlib.Path instead of os.path for filesystem operations
- Structure imports: stdlib → third-party → local (PEP 8)
- Use dataclasses (PEP 557) for simple data containers
- Prefer context managers (with) for resource handling
- Use structural pattern matching (PEP 634) for complex
- run ruff frequently

### Testing

- "hatch run test" command the entire testing suite

- anytime a new feature or refactor is done, we MUST find or make the golden/character test FIRST as a baseline standaard BEFORE starting, under no circumstance are you to not follow this pattern



## Available Agents:

1. **bug-context-analyzer** - Investigates precise context around bugs without suggesting fixes
2. **code-synthesis-analyzer** - Analyzes recent code changes to identify issues needing fixes
3. **documentation-synthesis-qa** - Creates comprehensive docs via multi-agent orchestration
4. **expert-debugger** - Debugs issues using strategic logging and root cause analysis
5. **phased-task-processor** - Breaks down markdown tasks into max 5 actionable phases
6. **prompt-engineer** - Optimizes prompts using 26 documented engineering principles
7. **rapid-code-synthesis-qa** - Quick quality assessment with confidence scores (1-5 scale)
8. **tech-docs-maintainer** - Updates docs in @documentation and .claude directories
