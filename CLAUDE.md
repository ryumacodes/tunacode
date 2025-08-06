### Documentation

- update the documents @documentation and in .claude after any update.


-  use the subagent tech-docs-maintainer to update the documentation you MUST instruct the subagent to keep doc updates short you will be PUNISHED for not telling the documentation agent to keep it to only the most distilled information

- always follow best practices with git commits naming and gh cli workflows

- commit frequently

- always be on the side of safety, if you have any question consult the user

### Python Coding Standards

- Use type hints (PEP 484) for all function signatures
- Prefer f-strings (PEP 498) over %-formatting or .format()
- Use pathlib.Path instead of os.path for filesystem operations
- Structure imports: stdlib → third-party → local (PEP 8)
- Use dataclasses (PEP 557) for simple data containers
- Prefer context managers (with) for resource handling
- Use structural pattern matching (PEP 634) for complex
- run ruff frequently

### Testing

- "make test" command the entire testing suite

- anytime a new feature or refactor is done, we MUST find or make the golden/character test FIRST as a baseline standaard BEFORE starting, under no circumstance are you to not follow this pattern

### Workflow

- before any updates make a git commit rollback point, clearly labeled for future agents

- the clear outline of the objective MUST be established before we begin ANY coding, do not under any circumstance begin any updates untill this is clearly understood, if you have any ambiuguity or quesiton, the user can be brought in or use best practises

- use scratchpad-multi.sh as you work, after the MD file is done being used sort it to the approate dir in /
