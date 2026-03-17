# Git Practices

## Purpose
This document defines safe Git operating practices for humans and code agents working in this repository.

Primary goal: preserve developer work while keeping commits clean and reviewable.

## Non-destructive Default (Hard Rule)
- Treat all untracked files/directories as potentially intentional work.
- Do **not** delete untracked files/directories by default.
- Do **not** run destructive cleanup commands (`git clean -fd`, `rm -rf`, bulk restores) unless the user explicitly asks.

## Required Process When New Files or Directories Appear
1. Detect and report: run `git status --short` and list what is new.
2. Classify with the user:
   - intentional project artifact
   - temporary/generated output
   - unknown
3. Ask for explicit confirmation before deletion or cleanup.
4. If confirmation is not provided, leave files in place.

## Pre-commit / Tooling Side Effects
Some hooks/tools may modify tracked files or create temporary outputs.

When this happens:
1. Report exactly what changed.
2. Revert only the files that were auto-modified **if requested**.
3. Do not remove untracked files/directories without confirmation.
4. Re-run checks after any requested revert.

## Safe Cleanup Policy
Cleanup is allowed only when one of the following is true:
- the user explicitly requested cleanup, or
- the repository has a documented generated-path policy and the path matches that policy.

If cleanup is authorized, state the exact command before running it.

## Commit Hygiene Checklist
Before commit/push:
- `git status --short` is reviewed.
- Commit scope matches the requested task.
- No unrelated local changes are included.
- Any untracked files are either intentionally kept or explicitly handled per user instruction.

## Related Docs
- `AGENTS.md`
- `HARNESS.md`
