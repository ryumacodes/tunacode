---
title: Dream Workflow
summary: High-level guidance for exploratory or aspirational design work.
when_to_read:
  - When exploring future ideas
  - When sketching possible directions before implementation
last_updated: "2026-04-04"
---

# Dream Work

Use this workflow for exploration, ideation, and rough shaping before there is
an implementation commitment.

This is not delivery work. It is a safe place for trying directions, comparing
approaches, and writing down possibilities without pretending they are already
approved or production-ready.

## Intent

Dream work exists to make exploration explicit instead of smuggling it into
feature or hotfix work. The output can be notes, sketches, branches, or
prototypes, but it should be clearly labeled as exploratory material.

## Working Rules

- Keep dream work on clearly labeled branches or worktrees.
- Make it obvious when something is exploratory rather than committed delivery.
- Prefer cheap experiments over deep implementation.
- Capture what was learned, even when the idea is rejected.
- Do not merge aspirational notes into operational docs as if they are current
  repository truth.

## Suitable Outputs

Dream work may produce:

- concept notes
- rough interface sketches
- prototype branches
- tradeoff comparisons
- future-work proposals

These artifacts are useful when they clarify a direction, eliminate a bad idea,
or sharpen the scope of later feature work.

## Verification

Dream work does not need production-grade verification, but it should still be
honest about its status.

Useful validation includes:

- proving whether an idea is technically feasible
- documenting what assumptions were tested
- separating observations from speculation
- linking any prototype behavior to the exact branch or artifact

## Done Criteria

Dream work is ready to hand off when all of the following are true:

- the exploratory status is clearly labeled
- the artifact captures concrete learning, not just vague enthusiasm
- any prototype scope is intentionally limited
- follow-on work, if any, is clear enough to convert into a feature or docs task
