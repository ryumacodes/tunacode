---
title: Debug Workflow
summary: Workflow guidance for reproducing, isolating, and fixing defects.
when_to_read:
  - When debugging a defect
  - When narrowing down a failing behavior
last_updated: "2026-04-04"
---

# Debug Work

Use this workflow when something is broken, ambiguous, or behaving differently
than expected.

The point of debugging is not to guess a likely fix and hope it works. The
point is to reduce uncertainty until the defect has a concrete reproduction,
clear boundaries, and a defensible correction.

## Intent

Debug work should move from symptom to cause in a way that leaves evidence
behind. The output is not just a patch. It is also an explanation of what
failed, how it was reproduced, and why the chosen fix is the right one.

Debugging in this repository should also leave behind the artifacts needed to
re-run or review the investigation later.

## Working Rules

- Start by reproducing the failure before changing code.
- Narrow the problem until the failing surface and likely cause are specific.
- Record the exact command, input, or environment needed to trigger the issue.
- Capture logs, traces, screenshots, or terminal output when they clarify the
  failure.
- Create parity or investigation artifacts when comparing expected versus
  actual behavior.
- Do not mix debugging with speculative cleanup or opportunistic refactors.
- Prefer evidence from traces, failing tests, or direct execution over
  intuition.

## Artifacts

Debug work should produce durable artifacts, not just a conclusion typed into
chat.

Preferred artifacts include:

- captured logs or trace output
- failing and passing command transcripts
- comparison notes for expected versus actual behavior
- parity artifacts under the repository's existing review or artifact paths

When a defect required side-by-side comparison, the parity artifact should make
the mismatch obvious enough that another person can inspect it without repeating
the entire investigation from scratch.

## Reproduction

Every defect should have a concrete reproduction path whenever possible.

Preferred reproduction forms include:

- a failing automated test
- a deterministic terminal command
- a concrete UI interaction path
- a captured input or artifact that triggers the problem

If the bug is intermittent, document what is known about the conditions that
make it more or less likely to occur.

## Verification

The fix is not complete until the original failure is shown to be resolved.

Preferred verification includes:

- the original failing test now passes
- the reproduction command no longer fails
- the user-facing path behaves correctly under the same conditions
- nearby or related behavior is checked for regression
- supporting logs or parity artifacts are preserved when they were part of the
  investigation

## Done Criteria

Debug work is ready when all of the following are true:

- the failure mode is clearly described
- reproduction steps or evidence are recorded
- logs or parity artifacts exist when they were needed to isolate the issue
- the fix addresses the demonstrated cause, not just the symptom surface
- verification proves the original issue is resolved
- the change does not bundle unrelated cleanup
