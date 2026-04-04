---
title: QA Workflow
summary: Workflow guidance for verifying behavior and validating changes after implementation.
when_to_read:
  - When running verification after a change
  - When checking behavior against expectations
last_updated: "2026-04-04"
---

# QA Work

Use this workflow when validating that a change is actually correct before
handoff, merge, or release.

QA work is not a formality. The job is to challenge assumptions, verify the
intended behavior, and surface remaining risks while there is still time to act
on them.

## Intent

The purpose of QA is to convert "it should work" into evidence about what does
work, what was checked, and what remains uncertain. Good QA reduces false
confidence and makes handoff clearer.

## Working Rules

- Verify the changed behavior directly instead of inferring success from style
  or type checks alone.
- Start with the most important user-facing or risk-heavy paths.
- Prefer deterministic tests and repeatable commands over ad hoc claims.
- Record what was checked and what was not checked.
- Surface residual risk instead of hiding it behind a partial green run.

## Coverage Expectations

QA should consider:

- the primary success path
- known failure paths
- nearby behavior with regression risk
- whether docs or operator guidance also need validation

Not every change needs exhaustive testing, but every change needs proportionate
evidence.

## Verification

Useful QA evidence includes:

- targeted automated tests
- manual reproduction of the affected user path
- lint, type, or architecture gates when relevant
- screenshots, logs, or terminal output when those artifacts clarify behavior

If a check is skipped, say so plainly and explain why.

## Done Criteria

QA work is ready when all of the following are true:

- the important changed behavior was actually exercised
- the verification method is concrete and repeatable
- remaining risks or untested areas are disclosed
- the evidence is strong enough for the scope of the change
- handoff can distinguish proven behavior from assumption
