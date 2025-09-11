---
allowed-tools: View, Bash(git:*), Bash(grep:*), Bash(jq:*), Bash(python:*), Bash(pytest:*), Bash(coverage:*), Bash(mypy:*), Bash(trivy:*), Bash(hadolint:*), Bash(dive:*), Bash(npm:*), Bash(lighthouse:*), Bash(kubectl:*), Bash(helm:*), Bash(curl:*), Bash(gh:*)
description: READ-ONLY QA focused FIRST on code-logic correctness of recent changes. Outlines issues/smells/antipatterns and risks. NO CODING, NO EDITS, NO FIXES.
writes-to: memory-bank/QA/
hard-guards:
  - Do not modify source files
  - Do not create commits/branches/PRs
  - Do not run formatters/linters in write mode
  - Produce findings & recommendations ONLY (outline, not code)
---

# QA (Read-Only) — Code Logic First

Run a post-execution QA review for: $ARGUMENTS  (topic OR path to plan/report)

## Initial Prompt (to user)
"I'm starting a **read-only** QA review focused on the **code logic of recent changes**. I will outline potential logic issues, smells/anti-patterns, and security concerns. **No coding or fixes will be performed.** Please provide a topic or the path to the plan/report under memory-bank/execute/."

## Strict Ordering
1) Locate artifacts → 2) Build change set (commit range & diff) → 3) Code-logic review (primary) → 4) Tests & contracts review → 5) Secondary scans (optional, read-only) → 6) Synthesize findings → 7) Save QA report

## Step 1 — Locate Inputs
- Resolve target by $ARGUMENTS:
  - If path given: use it.
  - If topic: select newest matching under `memory-bank/plan/` and `memory-bank/execute/`.
- Read FULLY (no offsets):
  - Plan: `memory-bank/plan/...`
  - Execution Log: `memory-bank/execute/*_log.md` (if exists)
  - Execution Report: `memory-bank/execute/*_report.md` (if exists)

## Step 2 — Build the Change Set (read-only)
- Determine commit range:
  - Start: from plan/log (`start_commit`) if available; else last tagged release or previous commit.
  - End: current HEAD (or end_commit in report).
- Capture diffs:
  - !`git diff --name-status <start>..<end>`
  - !`git diff --stat <start>..<end>`
  - !`git log --oneline <start>..<end>`
- Extract changed files (focus on src/ and tests/), group by module/package.
- For each changed file:
  - !`git diff <start>..<end> -- <file>` (context for evidence referencing only)

## Step 3 — Code-Logic Review (PRIMARY)
Evaluate only the changed areas, emphasizing control/data flow correctness.

Checklist (apply per module/file/function changed):
- **Inputs & Preconditions**: validation, type assumptions, null/empty, boundary values.
- **Control Flow**: branching completeness, unreachable paths, fall-through, early returns.
- **Data Flow**: invariant preservation, mutation scope, shared state leakage, aliasing risks.
- **State & Transactions**: idempotency, atomicity, rollback behavior, race/concurrency hazards.
- **Error Handling**: specific exceptions vs broad catches, retry/backoff, dead-letter paths.
- **Contracts**: pre/post-conditions, schema compatibility (request/response, DTOs), versioning.
- **Time/Locale**: timezones, monotonic clocks, DST, parsing/formatting stability.
- **Resource Hygiene**: file/conn lifecycle, timeouts, cancellation propagation.
- **Edge Cases**: empty sets, max sizes, pagination, partial failure scenarios.
- **Public Surface**: backward compatibility, OpenAPI/types alignment.

## Step 4 — Tests & Contracts (READ-ONLY)
- Map **each changed public function/endpoint** to test coverage:
  - !`pytest -q` (read result), !`coverage run -m pytest && coverage report --format=markdown`
  - Identify **missing cases**: error branches, boundary conditions, property invariants, mutation tests.
- Contract/API checks (if applicable):
  - OpenAPI/JSON schema drift vs implementations.
  - Client compatibility (breaking field/enum changes).

## Step 5 — Secondary Scans (Optional, Read-Only)
- Static/security summaries (no write/auto-fix):
  - `mypy` (report only), `bandit -r . -q || true`, `pip-audit` / `npm audit --json | jq`.
- Container & deploy context (if relevant): `hadolint`, `trivy`, `dive` summaries.
- Web (if staged): brief Lighthouse JSON summary for **regressions** only.

## Step 6 — Write QA Report
Create `memory-bank/QA/YYYY-MM-DD_HH-MM-SS_<topic>_qa.md` with:

---
title: "<topic> – QA Report (Code Logic First)"
phase: QA
date: "{{timestamp}}"
owner: "{{agent_or_user}}"
sources:
  plan: "memory-bank/plan/<file>.md"
  execution_log: "memory-bank/execute/<logfile>.md"
  execution_report: "memory-bank/execute/<reportfile>.md"
  commit_range: "<start>..<end>"
policy: "READ-ONLY QA — NO CODING OR CHANGES"
scope: "Changed code only (logic-first), plus impacted contracts/tests"
---

## 0. Summary Verdict
- Overall: ✅ Accept | ⚠️ Accept w/ Conditions | ❌ Reject
- Top logic risks (3–5 bullets)
- Required follow-ups (non-prescriptive)

## 1. Change Summary (What changed)
- Commit range: <start>..<end>
- Diffstat: <files/insertions/deletions>
- Modules touched:
  - `<pkg/module>` — files changed: n (list)
- User-visible behavior changes (from plan/report): bullets

## 2. Code-Logic Findings (by severity)
> Each item includes **Evidence (file:lines, commit)**, **Impact**, **Likelihood**, **Suggested Remediation (outline only)**, **Owner**, **Due-by**.

### Critical
- [CR-1] <title> — Evidence: `<file>#Lx-Ly` (commit `<sha>`), Impact: …, Likelihood: …
### High
